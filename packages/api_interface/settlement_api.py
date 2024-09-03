from decimal import Decimal
import datetime
import logging
import json

import packages.load_web3 as load_web3
import packages.load_config as load_config

from .contract_api import get_contract
from .util_api import is_valid_json

config = load_config.load_config()

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

logger = logging.getLogger(__name__)

def from_timestamp(ts):
    return None if ts == 0 else datetime.datetime.fromtimestamp(ts)

def get_settle_dict(settle, settle_idx, contract):
    try:
        settle_dict = {}
        settle_dict["extended_data"] = json.loads(settle[0].replace("'", '"'))
        settle_dict["settle_due_dt"] = from_timestamp(settle[1])
        settle_dict["transact_min_dt"] = from_timestamp(settle[2])
        settle_dict["transact_max_dt"] = from_timestamp(settle[3])
        settle_dict["transact_count"] = settle[4]
        settle_dict["advance_amt"] = f'{Decimal(settle[5]) / 100:.2f}'
        settle_dict["advance_amt_gross"] = f'{Decimal(settle[6]) / 100:.2f}'
        settle_dict["settle_pay_dt"] = from_timestamp(settle[7])
        settle_dict["settle_exp_amt"] = f'{Decimal(settle[8]) / 100:.2f}'
        settle_dict["settle_pay_amt"] = f'{Decimal(settle[9]) / 100:.2f}'
        settle_dict["settle_confirm"] = settle[10]
        settle_dict["dispute_amt"] = f'{Decimal(settle[11]) / 100:.2f}'
        settle_dict["dispute_reason"] = settle[12]
        settle_dict["days_late"] = settle[13]
        settle_dict["late_fee_amt"] = f'{Decimal(settle[14]) / 100:.2f}'
        settle_dict["residual_pay_dt"] = from_timestamp(settle[15])
        settle_dict["residual_pay_amt"] = f'{Decimal(settle[16]) / 100:.2f}'
        settle_dict["residual_confirm"] = settle[17]
        settle_dict["residual_exp_amt"] = f'{Decimal(settle[18]) / 100:.2f}'
        settle_dict["residual_calc_amt"] = f'{Decimal(settle[19]) / 100:.2f}'
        settle_dict["contract_idx"] = contract['contract_idx']
        settle_dict["contract_name"] = contract['contract_name']
        settle_dict["funding_instr"] = contract['funding_instr']
        settle_dict["settle_idx"] = settle_idx

        logger.debug("Settle exp amount (String): %s", settle_dict["settle_exp_amt"])
        logger.debug("Settle exp type: %s", type(settle_dict["settle_exp_amt"]))

        return settle_dict

    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error for settlement {settle_idx}: {str(e)}")
        raise RuntimeError(f"Failed to decode JSON for settlement {settle_idx}") from e
    except Exception as e:
        logger.error(f"Unexpected error processing settlement {settle_idx}: {str(e)}")
        raise RuntimeError(f"Failed to process settlement {settle_idx}") from e

def get_settlements(contract_idx):
    try:
        settlements = []
        contract = get_contract(contract_idx)
        settles = w3_contract.functions.getSettlements(contract['contract_idx']).call()

        for settle_idx, settle in enumerate(settles):
            settle_dict = get_settle_dict(settle, settle_idx, contract)
            settlements.append(settle_dict)

        sorted_settlements = sorted(settlements, key=lambda d: d['settle_due_dt'], reverse=False)
        return sorted_settlements

    except Exception as e:
        logger.error(f"Error retrieving settlements for contract {contract_idx}: {str(e)}")
        raise RuntimeError(f"Failed to retrieve settlements for contract {contract_idx}") from e

def add_settlements(contract_idx, settlements):
    validate_settlements(settlements)

    try:
        for settlement in settlements:
            due_dt = int(datetime.datetime.combine(settlement["settle_due_dt"], datetime.time.min).timestamp())
            min_dt = int(datetime.datetime.combine(settlement["transact_min_dt"], datetime.time.min).timestamp())
            max_dt = int(datetime.datetime.combine(settlement["transact_max_dt"], datetime.time.min).timestamp())
            extended_data = str(settlement["extended_data"])
            nonce = w3.eth.get_transaction_count(config["wallet_addr"])
            call_function = w3_contract.functions.addSettlement(contract_idx, extended_data, due_dt, min_dt, max_dt).build_transaction(
                {"from": config["wallet_addr"], "nonce": nonce, "gas": config["gas_limit"]})
            tx_receipt = load_web3.get_tx_receipt(call_function)
            if tx_receipt["status"] != 1:
                raise RuntimeError(f"Blockchain transaction failed for contract {contract_idx} settlement.")

        return True

    except Exception as e:
        logger.error(f"Error adding settlements for contract {contract_idx}: {str(e)}")
        raise RuntimeError(f"Failed to add settlements for contract {contract_idx}") from e

def delete_settlements(contract_idx):
    try:
        nonce = w3.eth.get_transaction_count(config["wallet_addr"])
        call_function = w3_contract.functions.deleteSettlements(contract_idx).build_transaction(
            {"from": config["wallet_addr"], "nonce": nonce, "gas": config["gas_limit"]})
        tx_receipt = load_web3.get_tx_receipt(call_function)
        if tx_receipt["status"] != 1:
            raise RuntimeError(f"Blockchain transaction failed for deleting settlements in contract {contract_idx}.")

        return True

    except Exception as e:
        logger.error(f"Error deleting settlements for contract {contract_idx}: {str(e)}")
        raise RuntimeError(f"Failed to delete settlements for contract {contract_idx}") from e

def validate_settlements(settlements):
    try:
        for settlement in settlements:
            if settlement['transact_min_dt'] >= settlement['transact_max_dt']:
                raise ValueError(f"Transaction minimum date must be less than maximum date. "
                                 f"Found: transact_min_dt={settlement['transact_min_dt']}, "
                                 f"transact_max_dt={settlement['transact_max_dt']}")

            if settlement['transact_max_dt'] > settlement['settle_due_dt']:
                raise ValueError(f"Transaction maximum date must be less than or equal to settlement due date. "
                                 f"Found: transact_max_dt={settlement['transact_max_dt']}, "
                                 f"settle_due_dt={settlement['settle_due_dt']}")

            if not is_valid_json(settlement["extended_data"]):
                raise ValueError(f"Invalid JSON for 'extended_data': '{settlement['extended_data']}'.")

    except ValueError as e:
        logger.error(f"Validation error in settlements: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during settlements validation: {str(e)}")
        raise