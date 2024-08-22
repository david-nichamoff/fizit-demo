import datetime
import os
import logging
import json

from decimal import Decimal, ROUND_DOWN

from packages.check_privacy import is_user_authorized

import packages.load_web3 as load_web3
import packages.load_config as load_config

from .party_api import get_contract_parties
from .util_api import is_valid_json

config = load_config.load_config()

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

def get_contract_count():
    return w3_contract.functions.getContractCount().call() 

def get_contract_dict(contract_idx):
    contract_dict, contract = {}, []
    contract = w3_contract.functions.getContract(contract_idx).call()

    contract_dict["extended_data"] = json.loads(contract[0].replace("'",'"'))
    contract_dict["contract_name"] = contract[1]
    contract_dict["contract_type"] = contract[2]
    contract_dict["funding_instr"] = json.loads(contract[3].replace("'",'"'))
    contract_dict["service_fee_pct"] = f'{Decimal(contract[4]) / 10000:.4f}'
    contract_dict["service_fee_max"] = f'{Decimal(contract[5]) / 10000:.4f}'
    contract_dict["service_fee_amt"] = f'{Decimal(contract[6]) / 100:.2f}'
    contract_dict["advance_pct"] = f'{Decimal(contract[7]) / 10000:.4f}'
    contract_dict["late_fee_pct"] = f'{Decimal(contract[8]) / 10000:.4f}'
    contract_dict["transact_logic"] = json.loads(contract[9].replace("'",'"'))
    contract_dict["min_threshold"] = f'{Decimal(contract[10]) / 100:.2f}'
    contract_dict["max_threshold"] = f'{Decimal(contract[11]) / 100:.2f}'
    contract_dict["notes"] = contract[12]
    contract_dict["is_active"] = contract[13]
    contract_dict["is_quote"] = contract[14]
    contract_dict["contract_idx"] = contract_idx

    logging.debug("Advance pct (Decimal): %s", contract_dict["advance_pct"])
    logging.debug("Advance pct type: %s", type(contract_dict["advance_pct"]))

    return contract_dict

def get_contracts(request):
    contracts = []
    for contract_idx in range(get_contract_count()):
        contract_dict = get_contract_dict(contract_idx)
        parties = get_contract_parties(contract_idx)
        if is_user_authorized(request, parties):
            contracts.append(contract_dict)

    return contracts

def get_contract(contract_idx):
    contract_dict = get_contract_dict(contract_idx)
    return contract_dict

def build_contract(contract_dict):

    # Validate the contract data before proceeding
    validate_contract_data(contract_dict)

    contract = []
    contract.append(str(contract_dict["extended_data"]))
    contract.append(contract_dict["contract_name"])
    contract.append(contract_dict["contract_type"])
    contract.append(str(contract_dict["funding_instr"]))
    contract.append(int(Decimal(contract_dict["service_fee_pct"]) * 10000))
    contract.append(int(Decimal(contract_dict["service_fee_max"]) * 10000))
    contract.append(int(Decimal(contract_dict["service_fee_amt"]) * 100))
    contract.append(int(Decimal(contract_dict["advance_pct"]) * 10000))
    contract.append(int(Decimal(contract_dict["late_fee_pct"]) * 10000))
    contract.append(str(contract_dict["transact_logic"]))
    contract.append(int(Decimal(contract_dict["min_threshold"]) * 100))
    contract.append(int(Decimal(contract_dict["max_threshold"]) * 100))
    contract.append(contract_dict["notes"])
    contract.append(contract_dict["is_active"])
    contract.append(contract_dict["is_quote"])
    return contract

def update_contract(contract_idx, contract_dict):
    contract = build_contract(contract_dict)
    nonce = w3.eth.get_transaction_count(config["wallet_addr"])
    call_function = w3_contract.functions.updateContract(contract_idx, contract).build_transaction(
        {"from":config["wallet_addr"],"nonce":nonce,"gas":config["gas_limit"]})
    tx_receipt = load_web3.get_tx_receipt(call_function)
    return True if tx_receipt["status"] == 1 else False

def add_contract(contract_dict):
    contract_idx = get_contract_count()
    contract = build_contract(contract_dict)
    nonce = w3.eth.get_transaction_count(config["wallet_addr"])
    call_function = w3_contract.functions.addContract(contract).build_transaction(
        {"from":config["wallet_addr"],"nonce":nonce,"gas":config["gas_limit"]})
    tx_receipt = load_web3.get_tx_receipt(call_function)
    return contract_idx if tx_receipt["status"] == 1 else False

def delete_contract(contract_idx):
    nonce = w3.eth.get_transaction_count(config["wallet_addr"])
    call_function = w3_contract.functions.deleteContract(contract_idx).build_transaction(
        {"from":config["wallet_addr"],"nonce":nonce,"gas":config["gas_limit"]})
    tx_receipt = load_web3.get_tx_receipt(call_function)
    return True if tx_receipt["status"] == 1 else False

def validate_contract_data(contract_dict):
    # Check if the provided contract type is valid
    valid_contract_types = ["ticketing", "advance", "construction"]
    if contract_dict["contract_type"] not in valid_contract_types:
        raise ValueError(
            f"Invalid contract type: '{contract_dict['contract_type']}'. "
            f"Valid types are: {', '.join(valid_contract_types)}."
        )

    # Check if the funding_instr.bank is valid
    if contract_dict["funding_instr"]["bank"] not in ['mercury']:
        raise ValueError(f"Invalid bank: '{contract_dict['funding_instr']['bank']}'. Valid banks are: 'mercury'.")

    # Check if the percentage fields are valid
    for field in ["service_fee_pct", "service_fee_max", "advance_pct", "late_fee_pct"]:
        if not isinstance(contract_dict[field], str) or not validate_percentage(contract_dict[field]):
            raise ValueError(f"Invalid value for '{field}': '{contract_dict[field]}'. Must be a string in the form X.XXXX and between 0.0000 and 1.0000.")

    # Check if the amount fields are valid
    for field in ["service_fee_amt", "max_threshold"]:
        if not isinstance(contract_dict[field], str) or not validate_amount(contract_dict[field]):
            raise ValueError(f"Invalid value for '{field}': '{contract_dict[field]}'. Must be a string in the form Y.XX where Y >= 0.")

    # Check if min_threshold is valid
    if not isinstance(contract_dict["min_threshold"], str) or not validate_amount(contract_dict["min_threshold"], allow_negative=True):
        raise ValueError(f"Invalid value for 'min_threshold': '{contract_dict['min_threshold']}.' Must be a string in the form Y.XX where Y can be any number (including negative).")

    # Check if transact_logic, extended_data, and transact_logic are valid JSON
    for field in ["transact_logic", "extended_data"]:
        if not is_valid_json(contract_dict[field]):
            raise ValueError(f"Invalid JSON for '{field}': '{contract_dict[field]}'.")

    # Check if is_active and is_quote are booleans
    for field in ["is_active", "is_quote"]:
        if not isinstance(contract_dict[field], bool):
            raise ValueError(f"Invalid value for '{field}': '{contract_dict[field]}'. Must be true or false.")

    # Check that min_threshold <= max_threshold
    if Decimal(contract_dict["min_threshold"]) > Decimal(contract_dict["max_threshold"]):
        raise ValueError(f"'min_threshold' ({contract_dict['min_threshold']}) must be less than or equal to 'max_threshold' ({contract_dict['max_threshold']}).")

    # Check that service_fee_max >= service_fee_pct
    if Decimal(contract_dict["service_fee_max"]) < Decimal(contract_dict["service_fee_pct"]):
        raise ValueError(f"'service_fee_max' ({contract_dict['service_fee_max']}) must be greater than or equal to 'service_fee_pct' ({contract_dict['service_fee_pct']}).")

    # Check if contract_name and notes are valid strings
    for field in ["contract_name", "notes"]:
        if not isinstance(contract_dict[field], str) or not contract_dict[field].strip():
            raise ValueError(f"Invalid value for '{field}': '{contract_dict[field]}'. Must be a non-empty string.")

def validate_percentage(value):
    try:
        decimal_value = Decimal(value)
        return 0 <= decimal_value <= 1 and len(value.split('.')[1]) == 4
    except (ValueError, IndexError):
        return False

def validate_amount(value, allow_negative=False):
    try:
        decimal_value = Decimal(value)
        if not allow_negative and decimal_value < 0:
            return False
        return len(value.split('.')[1]) == 2
    except (ValueError, IndexError):
        return False

