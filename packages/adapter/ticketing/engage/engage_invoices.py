import requests
import os
import datetime
import requests
import babel.numbers
import decimal
import time

import web3
from web3 import Web3
from web3.middleware import geth_poa_middleware

src_dict, dest_dict = {},{}

# Get api_key and ids for each src
with open("./src_bus_id.txt","r") as fin:
    lines = fin.readlines()

for line in lines:
    src_id, api_key, src_code, src_wallet = line.split(',')
    src_dict[src_id] = (api_key, src_code.strip(), src_wallet.strip())

# Get codes for each dest
with open("./dest_bus_id.txt","r") as fin:
    lines = fin.readlines()

for line in lines:
    dest_id, dest_code, dest_wallet = line.split(',')
    dest_dict[dest_id] =  (dest_code, dest_wallet.strip())

# current date and time
date_now = datetime.datetime.today().date()

# The base URI for all request
base_uri = "https://devapi.engage-m.com"

# Open a connection to Avalanche, get contract and abi
with open("./ava_rpc.txt","r") as fin:
    ava_rpc = fin.read()

with open("./ava_api_key.txt","r") as fin:
    ava_api_key = fin.read()

with open("./fizit_addr.txt","r") as fin:
    caller = fin.read().strip()

with open("./fizit_key.txt","r") as fin:
    private_key = fin.read().strip()

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

contract= w3.eth.contract(abi=abi,address=contract_addr)

with open("./invoice_id.txt","r") as fin:
    lines = fin.readlines()

for line in lines:
    src, dest, invoice_id = line.split(',')

    # Add the Authorization header
    headers = {'x-api-key' : src_dict[src][0], 'businessId' : src}

    # submit the invoice
    invoice_resp = requests.put(f'{base_uri}/invoicev1/invoiceGroup/' + str(invoice_id.strip()) + '/sourceSubmit',
                                headers=headers, params={"source_business_id" : src})
    invoice_dict = invoice_resp.json()
    print (invoice_dict)
    
    if invoice_dict['success'] == 'true':
        print ("Successfully submitted invoice " + str(invoice_id.strip()))

        # add this invoice to the contract on Avalanche
        invoice_struct = [str(invoice_dict['data']['custom_cd']), int(time.mktime(date_now.timetuple())),
                          int(round(invoice_dict['data']['total'], 2) * 100)]
        nonce = w3.eth.get_transaction_count(caller)
        call_function = contract.functions.addInvoice(dest_dict[dest][1],invoice_struct).build_transaction({"from":caller,"nonce":nonce})
        signed_tx = w3.eth.account.sign_transaction(call_function, private_key=private_key)
        send_tx = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(send_tx)
        print(tx_receipt)
    else:
        print ("Error submitting invoice " + str(invoice_id.strip()))

with open("./invoice_id.txt","w") as fout:
    pass
