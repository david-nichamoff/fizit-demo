from decimal import Decimal
import datetime
import logging

import json

from packages.check_privacy import is_user_authorized

import packages.load_web3 as load_web3
import packages.load_config as load_config

from .contract_api import get_contract
from .util_api import is_valid_json

config = load_config.load_config()

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

def from_timestamp(ts):
    return None if ts == 0 else datetime.datetime.fromtimestamp(ts)

    from decimal import Decimal, ROUND_DOWN

def get_settle_dict(settle, settle_idx, contract):
    settle_dict = {}
    settle_dict["extended_data"] = json.loads(settle[0].replace("'",'"'))
    settle_dict["settle_due_dt"] = from_timestamp(settle[1]) 
    settle_dict["transact_min_dt"] = from_timestamp(settle[2])
    settle_dict["transact_max_dt"] = from_timestamp(settle[3])
    settle_dict["transact_count"] = settle[4]
    settle_dict["settle_pay_dt"] = from_timestamp(settle[5])
    settle_dict["settle_exp_amt"] = f'{Decimal(settle[6]) / 100:.2f}'
    settle_dict["settle_pay_amt"] = f'{Decimal(settle[7]) / 100:.2f}'
    settle_dict["settle_confirm"] = settle[8]
    settle_dict["dispute_amt"] = f'{Decimal(settle[9]) / 100:.2f}'
    settle_dict["dispute_reason"] = settle[10]
    settle_dict["days_late"] = settle[11]
    settle_dict["late_fee_amt"] = f'{Decimal(settle[12]) / 100:.2f}'
    settle_dict["residual_pay_dt"] = from_timestamp(settle[13]) 
    settle_dict["residual_pay_amt"] = f'{Decimal(settle[14]) / 100:.2f}'
    settle_dict["residual_confirm"] = settle[15]
    settle_dict["residual_exp_amt"] = f'{Decimal(settle[16]) / 100:.2f}'
    settle_dict["residual_calc_amt"] = f'{Decimal(settle[17]) / 100:.2f}'
    settle_dict["contract_idx"] = contract['contract_idx']
    settle_dict["contract_name"] = contract['contract_name']
    settle_dict["funding_instr"] = contract['funding_instr']
    settle_dict["settle_idx"] = settle_idx

    logging.debug("Settle exp amount (String): %s", settle_dict["settle_exp_amt"])
    logging.debug("Settle exp type: %s", type(settle_dict["settle_exp_amt"]))

    return settle_dict

def get_contract_settlements(contract_idx):
    settlements = []
    contract = get_contract(contract_idx)
    settles = w3_contract.functions.getSettlements(contract['contract_idx']).call() 
    for settle in settles:
        settle_dict = get_settle_dict(settle, len(settlements), contract)
        settlements.append(settle_dict)

    sorted_settlements = sorted(settlements, key=lambda d: d['settle_due_dt'], reverse=False)
    return sorted_settlements 

def add_settlements(contract_idx, settlements):
    validate_settlements(settlements)

    for settlement in settlements:
        due_dt = int(datetime.datetime.combine(settlement["settle_due_dt"], datetime.time.min).timestamp())
        min_dt = int(datetime.datetime.combine(settlement["transact_min_dt"], datetime.time.min).timestamp())
        max_dt = int(datetime.datetime.combine(settlement["transact_max_dt"], datetime.time.min).timestamp())
        extended_data = str(settlement["extended_data"])
        nonce = w3.eth.get_transaction_count(config["wallet_addr"])
        call_function = w3_contract.functions.addSettlement(contract_idx, extended_data, due_dt, min_dt, max_dt).build_transaction(
            {"from":config["wallet_addr"],"nonce":nonce,"gas":config["gas_limit"]}) 
        tx_receipt = load_web3.get_tx_receipt(call_function)
        if tx_receipt["status"] != 1: return False
    return True

def delete_settlements(contract_idx):
    nonce = w3.eth.get_transaction_count(config["wallet_addr"])
    call_function = w3_contract.functions.deleteSettlements(contract_idx).build_transaction(
        {"from":config["wallet_addr"],"nonce":nonce,"gas":config["gas_limit"]}) 
    tx_receipt = load_web3.get_tx_receipt(call_function)
    return True if tx_receipt["status"] == 1 else False   

def validate_settlements(settlements):
    for settlement in settlements:
        # Check if transact_min_dt < transact_max_dt
        if settlement['transact_min_dt'] >= settlement['transact_max_dt']:
            raise ValueError(f"Transaction minimum date must be less than maximum date. "
                             f"Found: transact_min_dt={settlement['transact_min_dt']}, "
                             f"transact_max_dt={settlement['transact_max_dt']}")

        # Check if transact_max_dt <= settle_due_dt
        if settlement['transact_max_dt'] > settlement['settle_due_dt']:
            raise ValueError(f"Transaction maximum date must be less than or equal to settlement due date. "
                             f"Found: transact_max_dt={settlement['transact_max_dt']}, "
                             f"settle_due_dt={settlement['settle_due_dt']}")

        # Check if extended_data is valid JSON
    for field in ["extended_data"]:
        if not is_valid_json(settlement[field]):
            raise ValueError(f"Invalid JSON for '{field}': '{settlement[field]}'.")