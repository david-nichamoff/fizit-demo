import requests
from datetime import datetime, timedelta

import packages.load_keys as load_keys
import packages.load_config as load_config

keys = load_keys.load_keys()
config = load_config.load_config()

def get_tickets(contract, engage_src, engage_dest, start_date, end_date):
    tickets = []
    url = f'{config["engage_uri"]}/v2/tickets'
    headers = {
        'x-api-key': engage_src.api_key,
        'businessID': str(engage_src.src_id),  
        'Content-Type': 'application/json'  
    }
    params = {"approvedate_before": end_date.strftime('%Y-%m-%d'), 
              "approvedate_after" : start_date.strftime('%Y-%m-%d')}
    response = requests.get(url, headers=headers, params=params)

    for engage_ticket in response.json()["data"]:
        engage_detail = requests.get(f'{config["engage_uri"]}/v2/tickets/' + str(engage_ticket['ID']) + '/tali', headers=headers).json()["data"]
        ticket = {
            "contract_idx"  : contract["contract_idx"],
            "contract_name" : contract["contract_name"],
            "ticket_id"     : engage_detail["ticketID"],
            "approved_dt"   : engage_detail["approveDate"],
            "ticket_amt"    : round(engage_detail["totalAmount"], 2),
            "ticket_data"   : engage_detail,
        }
        tickets.append(ticket)

    return tickets

def get_invoices(contract, engage_src, engage_dest, start_date, end_date):
    invoices = []
    url = f'{config["engage_uri"]}/invoicev1/invoiceGroup'
    headers = {
        'x-api-key': engage_src.api_key,
        'businessID': str(engage_src.src_id),  
        'Content-Type': 'application/json'  
    }
    invoice_list = requests.get(url, headers=headers).json()["data"]
    print(invoice_list)

    for invoice in invoice_list:
        invoice = {
             "contract_idx"  : contract["contract_idx"],
             "contract_name" : contract["contract_name"],
 #            "invoice_data"  : invoice_detail 
         }

        invoices.append(invoice)
        curr_date += timedelta(days=1)

    return invoices

def add_invoice():
    pass