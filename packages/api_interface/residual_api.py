import datetime
from decimal import Decimal
import logging

import adapter.bank.mercury

import packages.load_web3 as load_web3
import packages.load_config as load_config

from .settlement_api import get_settlements
from .contract_api import get_contract

config = load_config.load_config()

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

logger = logging.getLogger(__name__)

def from_timestamp(ts):
    return None if ts == 0 else datetime.datetime.fromtimestamp(ts)

def get_residuals(contract_idx):
    try:
        residuals = []
        settlements = get_settlements(contract_idx)
        contract = get_contract(contract_idx)

        for settle in settlements:
            if settle["residual_pay_amt"] == "0.00" and Decimal(settle["residual_calc_amt"]) > Decimal(0.00):
                residual_dict = {
                    "contract_idx": contract["contract_idx"],
                    "settle_idx": settle["settle_idx"],
                    "bank": contract["funding_instr"]["bank"],
                    "account_id": contract["funding_instr"]["account_id"],
                    "recipient_id": contract["funding_instr"]["recipient_id"],
                    "residual_calc_amt": settle["residual_calc_amt"]
                }
                residuals.append(residual_dict)

        return residuals

    except Exception as e:
        logger.error(f"Error retrieving residuals for contract {contract_idx}: {str(e)}")
        raise RuntimeError(f"Failed to retrieve residuals for contract {contract_idx}") from e

def add_residuals(contract_idx, residuals):
    if not residuals:
        return True

    try:
        contract = get_contract(contract_idx)

        for residual in residuals:
            try:
                bank_adapter = getattr(adapter.bank, residual["bank"])
                success, error_message = bank_adapter.make_payment(residual["account_id"], residual["recipient_id"], residual["residual_calc_amt"])

                if not success:
                    raise ValueError(f"Payment failed: {error_message}")

                nonce = w3.eth.get_transaction_count(config["wallet_addr"])
                current_time = int(datetime.datetime.now().timestamp())
                payment_amt = int(Decimal(residual["residual_calc_amt"]) * 100)

                call_function = w3_contract.functions.payResidual(
                    contract_idx, residual["settle_idx"], current_time, payment_amt, "completed"
                ).build_transaction({
                    "from": config["wallet_addr"],
                    "nonce": nonce,
                    "gas": config["gas_limit"]
                })

                tx_receipt = load_web3.get_tx_receipt(call_function)
                if tx_receipt["status"] != 1:
                    raise RuntimeError("Transaction failed on the blockchain.")

            except AttributeError as e:
                logger.error(f"Bank adapter error: {str(e)}")
                raise RuntimeError(f"Bank adapter error: {str(e)}")

        return True

    except Exception as e:
        logger.error(f"Error adding residuals for contract {contract_idx}: {str(e)}")
        raise