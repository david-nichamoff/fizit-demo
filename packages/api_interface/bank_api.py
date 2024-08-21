from json_logic import jsonLogic

import adapter.bank.mercury

import packages.load_web3 as load_web3
import packages.load_config as load_config

config = load_config.load_config()

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

def get_accounts(bank):
    if bank == "mercury" or bank is None:  
        accounts = adapter.bank.mercury.get_accounts()
    return accounts

def get_recipients(bank):
    if bank == "mercury" or bank is None:
        recipients = adapter.bank.mercury.get_recipients()
    return recipients

def get_deposits(start_date, end_date, account_id):
    deposits = adapter.bank.mercury.get_deposits(start_date, end_date, account_id)
    return deposits