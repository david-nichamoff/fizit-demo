import datetime
import logging
from decimal import Decimal

import adapter.bank.mercury

import packages.load_web3 as load_web3
import packages.load_config as load_config

from .transaction_api import get_transactions
from .contract_api import get_contract_count, get_contract

config = load_config.load_config()

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

logger = logging.getLogger(__name__)

def from_timestamp(ts):
    return None if ts == 0 else datetime.datetime.fromtimestamp(ts)

def get_deposits(start_date, end_date, contract_idx):
    try:
        contract = get_contract(contract_idx)
        bank_adapter = getattr(adapter.bank, contract["funding_instr"]["bank"])
        deposits = bank_adapter.get_deposits(start_date, end_date, contract)
        return deposits
    except AttributeError as e:
        logger.error(f"Bank adapter error for contract {contract_idx}: {str(e)}")
        raise ValueError(f"Unsupported bank: {contract['funding_instr']['bank']}") from e
    except Exception as e:
        logger.error(f"Error retrieving deposits for contract {contract_idx}: {str(e)}")
        raise RuntimeError(f"Failed to retrieve deposits for contract {contract_idx}") from e

def add_deposits(contract_idx, deposits):
    try:
        contract = get_contract(contract_idx)

        for deposit in deposits:
            print(deposit)
            try:
                # Convert deposit_amt to an integer representing cents
                payment_amt = int(Decimal(deposit["deposit_amt"]) * 100)

                # Use deposit_dt and set the time to midnight UTC
                settlement_date = deposit["deposit_dt"].replace(hour=0, minute=0, second=0, microsecond=0)
                settlement_timestamp = int(settlement_date.timestamp())

                # Extract the necessary values
                settle_idx = deposit["settle_idx"]
                settle_confirm = deposit["settle_confirm"]
                dispute_reason = deposit["dispute_reason"]

                nonce = w3.eth.get_transaction_count(config["wallet_addr"])
                call_function = w3_contract.functions.postSettlement(
                    contract_idx, settle_idx, settlement_timestamp, payment_amt, settle_confirm, dispute_reason
                ).build_transaction({
                    "from": config["wallet_addr"],
                    "nonce": nonce,
                    "gas": config["gas_limit"]
                })

                tx_receipt = load_web3.get_tx_receipt(call_function)
                if tx_receipt["status"] != 1:
                    raise RuntimeError(f"Transaction failed with status: {tx_receipt['status']}")

            except AttributeError as e:
                logger.error(f"AttributeError in add_deposits for contract {contract_idx}: {str(e)}")
                raise RuntimeError(f"Failed to process deposit {deposit['deposit_id']} for contract {contract_idx}") from e
            except Exception as e:
                logger.error(f"Error in add_deposits for contract {contract_idx}: {str(e)}")
                raise RuntimeError(f"Failed to add deposit {deposit['deposit_id']} for contract {contract_idx}") from e

    except Exception as e:
        logger.error(f"Error in add_deposits for contract {contract_idx}: {str(e)}")
        raise RuntimeError(f"Failed to add deposits for contract {contract_idx}") from e

    return True