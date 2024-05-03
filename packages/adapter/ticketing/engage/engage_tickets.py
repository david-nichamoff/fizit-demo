import requests
import os
import datetime
import time
import babel.numbers
import decimal

import web3
from web3 import Web3
from web3.middleware import geth_poa_middleware

# src_dict = valid haulers (src)
# dest_dict = valid destinations
# pymt_dict = payments for each hauler
src_dict, dest_dict, pymt_dict = {}, {}, {}

# Get api_key and codes for each src
with open("./src_bus_id.txt","r") as fin:
    lines = fin.readlines()

for line in lines:
    src_id, api_key, src_code, src_wallet = line.split(',')
    src_dict[src_id] = (api_key, src_code.strip(), src_wallet.strip())
    pymt_dict[src_id] = 0

# Get codes for each dest
with open("./dest_bus_id.txt","r") as fin:
    lines = fin.readlines()

for line in lines:
    dest_id, dest_code, dest_wallet = line.split(',')
    dest_dict[dest_id] =  (dest_code, dest_wallet)

# The base URI for all request
base_uri = "https://devapi.engage-m.com"

# Retrieve all of the Avalanche connection parameters
with open("./ava_rpc.txt","r") as fin:
    ava_rpc = fin.read()

with open("./ava_api_key.txt","r") as fin:
    ava_api_key = fin.read()

with open("./fizit_addr.txt","r") as fin:
    caller = fin.read().strip()

with open("./fizit_key.txt","r") as fin:
    private_key = fin.read().strip()

# Open a connection to Avalanche, get contract and abi
w3 = Web3(Web3.HTTPProvider(ava_rpc + "/" + ava_api_key))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

if w3.is_connected():
    print("Connection successful")
else:
    print ("Connection failed")

with open("./engage_contract_addr.txt","r") as fin:
    contract_addr = fin.read().strip()

with open("./engage_abi.txt","r") as fin:
    abi = fin.read()

contract = w3.eth.contract(abi=abi,address=contract_addr)

# Get funded percentage and FIZIT fee percentage
fee_int = contract.functions.FEE_PCT().call()
funded_int = contract.functions.FUNDED_PCT().call()

# fee is of the form XYY where the value is X.YY%
fee_pct = float(fee_int) / pow(10, len(str(fee_int)) + 1)
funded_pct = float(funded_int) / 100

# Get the last date run, date to start will be the next day
with open("./last_ticket_dt.txt", "r") as fin:
    date_start = datetime.datetime.strptime(str.rstrip(fin.read()), '%Y-%m-%d') + datetime.timedelta(days=1)

# Get current date and send date_end to yesterday
date_now = datetime.datetime.today().date()
date_end = date_now + datetime.timedelta(days=-1)
curr_date = date_start.date() 

# Get last invoice number used
with open("./last_invoice_no.txt","r") as fin:
    invoice_no = int(fin.read().strip())

# Loop through all of the days from the start to yesterday
while curr_date <= date_end:
    print (str(curr_date))

    # Loop through all of the haulers 
    for src in src_dict:

        # Add the Authorization header and get all tickets for curr_date from current src/payee
        headers = {'x-api-key' : src_dict[src][0], 'businessId' : src}
        tickets_dict = requests.get(f'{base_uri}/v2/tickets', headers=headers, params={"approvedate_date":curr_date}).json()

        for ticket in tickets_dict['data']:
            ticket_dict = requests.get(f'{base_uri}/v2/tickets/' + str(ticket['ID']) + '/tali', headers=headers).json()
            ticket_amt = round(ticket_dict['data']['totalAmount'], 2)

            if ticket_amt > 0:

              # Calculate payment amounts
              fee_amt = round(ticket_amt * fee_pct, 2)
              init_paid_amt = round((ticket_amt * funded_pct) - fee_amt)

              # Find the destination for this ticket, but only pay if dest dict is on our list of approved dest
              if str(ticket_dict['data']['pickUpBusinessID']) in dest_dict:
                  pymt_dict[src] += init_paid_amt

              # Find if there is a current open invoice 
              invoice_dict = requests.get(f'{base_uri}/invoicev1/invoiceGroup', headers=headers, 
                      params={"destination_business_id":ticket_dict['data']['pickUpBusinessID'], "invoice_status_name":"New"}).json()

              if invoice_dict['count'] > 0: 
                  invoice_group_id = invoice_dict['data'][0]['id']
                  print ("Found existing open invoice " + str(invoice_group_id))

              # add an invoice if there is not one already
              else:  # invoice_dict['count'] == 0
                  for retry in range(10):
                      try:
                          invoice_dict = requests.post(f'{base_uri}/invoicev1/invoiceGroup', headers=headers,
                                                       params = {'source_business_id' : src,
                                                                 'destination_business_id':ticket_dict['data']['pickUpBusinessID'],
                                                                 'custom_cd' : 'FIZIT_' + str(invoice_no),
                                                                 'invoice_date' : str(date_now)}).json()
                          invoice_group_id = invoice_dict['data']['id']
                          break
                      except KeyError:
                          invoice_no += 1

                  invoice_group_id = invoice_dict['data']['id']
                  print ("Added new invoice " + str(invoice_group_id))

                  # write the invoice number to a file so it can be closed later
                  with open("./invoice_id.txt","a") as fout:
                      fout.write(str(src) + "," + str(ticket_dict['data']['pickUpBusinessID']) + "," + 
                                 str(invoice_group_id) + "\n")

              # add this ticket to the invoice group 
              # we will ignore 0 amount and negative tickets
              data= { "engage_ticket" : [str(ticket_dict['data']['jobNo'])] }
              invoice_dict = requests.post(f'{base_uri}/invoicev1/invoiceGroup/'+ str(invoice_group_id)+'/assignEngageTicket',
                              headers=headers, params=data).json()
              print ("Added ticket " + str(ticket['ID']) + " to invoice " + str(invoice_group_id))

              # save the PDF image of the ticket 
              response = requests.get(f'{base_uri}/v2/tickets/' + str(ticket['ID']) + '/pdf', headers=headers)
              with open('./ticket/' + str(ticket['ID']) + '.pdf', "wb") as fout:
                  fout.write(response.content)

              # add this ticket to the contract on Avalanche 
              ticket_struct = [str(ticket_dict['data']['jobNo']),         # ticket_no 
                               int(time.mktime(curr_date.timetuple())),   # approved_dt
                               int(time.mktime(date_now.timetuple())),    # init_paid_dt 
                               int(init_paid_amt),                        # init_paid_amt
                               0, 0,                                      # res_paid_dt, res_paid_amt
                               ticket_amt,                                # ticket_amt
                               fee_amt,                                   # fee_amt
                               '','']                                     # adj_reason, nid

              nonce = w3.eth.get_transaction_count(caller)
              call_function = contract.functions.addTicket(src_dict[src][2],ticket_struct).build_transaction({"from":caller,"nonce":nonce})
              signed_tx = w3.eth.account.sign_transaction(call_function, private_key=private_key) 
              send_tx = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
              tx_receipt = w3.eth.wait_for_transaction_receipt(send_tx) 
              print(tx_receipt)
            elif ticket_amt <  0:
              print ("Negative dollar ticket " + str(ticket['ID'])) 
            else:  # ticket_amt ==  0
              print ("Zero dollar ticket " + str(ticket['ID'])) 

    # move to the next day
    curr_date = curr_date + datetime.timedelta(days=1)

for src in pymt_dict:
    if pymt_dict[src] > 0:
        with open("./invoice/" + str(curr_date) + ".txt", "w") as fout:
            fout.write(src_dict[src][1] + "," + str(round(pymt_dict[src], 2)))

with open("./last_ticket_dt.txt", "w") as fout:
    fout.write(str(date_end))

with open("./last_invoice_no.txt", "w") as fout:
    fout.write(str(invoice_no))
