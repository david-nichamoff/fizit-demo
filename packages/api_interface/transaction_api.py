from decimal import Decimal
from datetime import datetime
import logging
import json
from json_logic import jsonLogic

import packages.load_web3 as load_web3
import packages.load_config as load_config

from .contract_api import get_contract
from .util_api import is_valid_json

config = load_config.load_config()

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

logger = logging.getLogger(__name__)

def from_timestamp(ts):
    return None if ts == 0 else datetime.fromtimestamp(ts)

def get_transact_dict(transact, transact_idx, contract):
    try:
        transact_dict = {
            "extended_data": json.loads(transact[0].replace("'", '"')),
            "transact_dt": from_timestamp(transact[1]),
            "transact_amt": f'{Decimal(transact[2]) / 100:.2f}',
            "service_fee_amt": f'{Decimal(transact[3]) / 100:.2f}',
            "advance_amt": f'{Decimal(transact[4]) / 100:.2f}',
            "transact_data": json.loads(transact[5].replace("'", '"')),
            "advance_pay_dt": from_timestamp(transact[6]),
            "advance_pay_amt": f'{Decimal(transact[7]) / 100:.2f}',
            "advance_confirm": transact[8],
            "contract_idx": contract['contract_idx'],
            "funding_instr": contract['funding_instr'],
            "transact_idx": transact_idx
        }
        logger.debug("Transaction amount (String): %s", transact_dict["transact_amt"])
        logger.debug("Transaction amount type: %s", type(transact_dict["transact_amt"]))

        return transact_dict
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.error(f"Error creating transaction dictionary: {str(e)}")
        raise ValueError(f"Invalid transaction data: {str(e)}")

def get_transactions(contract_idx, transact_min_dt=None, transact_max_dt=None):
    try:
        transactions = []
        contract = get_contract(contract_idx)

        transacts = w3_contract.functions.getTransactions(contract['contract_idx']).call() 
        for transact in transacts:
            transact_dict = get_transact_dict(transact, len(transactions), contract)
            transact_dt = transact_dict['transact_dt']

            if transact_min_dt and transact_dt < transact_min_dt:
                continue  # Skip transactions before the minimum date
            if transact_max_dt and transact_dt >= transact_max_dt:
                continue  # Skip transactions after the maximum date

            transactions.append(transact_dict)

        sorted_transactions = sorted(transactions, key=lambda d: d['transact_dt'], reverse=True)
        return sorted_transactions
    except Exception as e:
        logger.error(f"Error retrieving transactions for contract {contract_idx}: {str(e)}")
        raise RuntimeError(f"Failed to retrieve transactions for contract {contract_idx}") from e

def add_transactions(contract_idx, transact_logic, transactions):
    validate_transactions(transactions)

    try:
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
                raise RuntimeError(f"Failed to add transaction for contract {contract_idx}. Transaction status: {tx_receipt['status']}")

        return True
    except Exception as e:
        logger.error(f"Error adding transactions for contract {contract_idx}: {str(e)}")
        raise RuntimeError(f"Failed to add transactions for contract {contract_idx}") from e

def delete_transactions(contract_idx):
    try:
        nonce = w3.eth.get_transaction_count(config["wallet_addr"])
        call_function = w3_contract.functions.deleteTransactions(contract_idx).build_transaction(
            {"from": config["wallet_addr"], "nonce": nonce, "gas": config["gas_limit"]}
        )
        tx_receipt = load_web3.get_tx_receipt(call_function)
        if tx_receipt["status"] != 1:
            raise RuntimeError(f"Failed to delete transactions for contract {contract_idx}. Transaction status: {tx_receipt['status']}")

        return True
    except Exception as e:
        logger.error(f"Error deleting transactions for contract {contract_idx}: {str(e)}")
        raise RuntimeError(f"Failed to delete transactions for contract {contract_idx}") from e

def validate_transactions(transactions):
    try:
        for transaction in transactions:
            # Validate extended_data as valid JSON
            if not is_valid_json(transaction.get("extended_data", "")):
                raise ValueError(f"Invalid JSON for 'extended_data': {transaction['extended_data']}")

            # Validate transact_data as valid JSON
            if not is_valid_json(transaction.get("transact_data", "")):
                raise ValueError(f"Invalid JSON for 'transact_data': {transaction['transact_data']}")
    except ValueError as e:
        logger.error(f"Transaction validation error: {str(e)}")
        raise