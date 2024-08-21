from decimal import Decimal
from datetime import datetime
import logging

import json
from json_logic import jsonLogic

import packages.load_web3 as load_web3
import packages.load_config as load_config

from .contract_api import get_contracts, get_contract

from .util_api import is_valid_json

config = load_config.load_config()

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

def from_timestamp(ts):
    return None if ts == 0 else datetime.fromtimestamp(ts)

def get_transact_dict(transact, transact_idx, contract):
    transact_dict = {}
    transact_dict["extended_data"] = json.loads(transact[0].replace("'", '"'))
    transact_dict["transact_dt"] = from_timestamp(transact[1])
    transact_dict["transact_amt"] = f'{Decimal(transact[2]) / 100:.2f}'
    transact_dict["advance_amt"] = f'{Decimal(transact[3]) / 100:.2f}'
    transact_dict["transact_data"] = json.loads(transact[4].replace("'", '"'))
    transact_dict["advance_pay_dt"] = from_timestamp(transact[5])
    transact_dict["advance_pay_amt"] = f'{Decimal(transact[6]) / 100:.2f}'
    transact_dict["advance_confirm"] = transact[7]
    transact_dict["contract_idx"] = contract['contract_idx']
    transact_dict["funding_instr"] = contract['funding_instr']
    transact_dict["transact_idx"] = transact_idx

    logging.debug("Transaction amount (String): %s", transact_dict["transact_amt"])
    logging.debug("Transaction amount type: %s", type(transact_dict["transact_amt"]))

    return transact_dict

def get_contract_transactions(contract_idx, transact_min_dt=None, transact_max_dt=None):
    transactions = []
    contract = get_contract(contract_idx)

    if len(contract) > 0:
        transacts = w3_contract.functions.getTransactions(contract['contract_idx']).call() 
        for transact in transacts:
            transact_dict = get_transact_dict(transact, len(transactions), contract)

            transact_dt = transact_dict['transact_dt']
            
            if transact_min_dt:
                if transact_dt < transact_min_dt:
                    continue  # Skip transactions before the minimum date
            if transact_max_dt:
                if transact_dt >= transact_max_dt:
                    continue  # Skip transactions after the maximum date
            transactions.append(transact_dict)

    sorted_transactions = sorted(transactions, key=lambda d: d['transact_dt'], reverse=True)
    return sorted_transactions

def add_transactions(contract_idx, transact_logic, transactions):
    validate_transactions(transactions)

    for transaction in transactions:
        extended_data = str(transaction["extended_data"])
        transact_dt = int(transaction["transact_dt"].timestamp())
        transact_data = transaction["transact_data"]

        # Check if 'adj' is in transact_data for adjustment
        if "adj" in transact_data:
            transact_amt = int(Decimal(transact_data["adj"]) * 100)
        else:
            transact_amt = int(jsonLogic(transact_logic, transact_data) * 100)

        nonce = w3.eth.get_transaction_count(config["wallet_addr"])
        call_function = w3_contract.functions.addTransaction(
            contract_idx, extended_data, transact_dt, transact_amt, str(transact_data)
        ).build_transaction(
            {"from": config["wallet_addr"], "nonce": nonce, "gas": config["gas_limit"]}
        )
        tx_receipt = load_web3.get_tx_receipt(call_function)
        if tx_receipt["status"] != 1:
            return False
    return True

def delete_transactions(contract_idx):
    nonce = w3.eth.get_transaction_count(config["wallet_addr"])
    call_function = w3_contract.functions.deleteTransactions(contract_idx).build_transaction(
        {"from":config["wallet_addr"],"nonce":nonce,"gas":config["gas_limit"]}) 
    tx_receipt = load_web3.get_tx_receipt(call_function)
    return True if tx_receipt["status"] == 1 else False   

def validate_transactions(transactions):
    pass

def validate_transactions(transactions):
    for transaction in transactions:
        # Validate extended_data as valid JSON
        if not is_valid_json(transaction.get("extended_data", "")):
            raise ValueError(f"Invalid JSON for 'extended_data': {transaction['extended_data']}")

        # Validate transact_data as valid JSON
        if not is_valid_json(transaction.get("transact_data", "")):
            raise ValueError(f"Invalid JSON for 'transact_data': {transaction['transact_data']}")