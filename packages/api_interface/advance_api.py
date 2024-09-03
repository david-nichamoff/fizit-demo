import datetime
import logging

import adapter.bank.mercury

from decimal import Decimal

import packages.load_web3 as load_web3
import packages.load_config as load_config

from .transaction_api import get_transactions
from .contract_api import get_contract

config = load_config.load_config()

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

logger = logging.getLogger(__name__)

def from_timestamp(ts):
    return None if ts == 0 else datetime.datetime.fromtimestamp(ts)

def get_advances(contract_idx):
    advances = []
    transactions = get_transactions(contract_idx)
    contract = get_contract(contract_idx)

    for transact in transactions:
        if transact["advance_pay_amt"] == "0.00" and Decimal(transact["advance_amt"]) > Decimal(0.00):
            advance_dict = {
                "contract_idx": contract["contract_idx"],
                "transact_idx": transact["transact_idx"],
                "bank": contract["funding_instr"]["bank"],
                "account_id": contract["funding_instr"]["account_id"],
                "recipient_id": contract["funding_instr"]["recipient_id"],
                "advance_amt": transact["advance_amt"]
            }
            advances.append(advance_dict)

    return advances

def add_advances(contract_idx, advances):
    contract = get_contract(contract_idx)

    for advance in advances:
        try:
            bank_adapter = getattr(adapter.bank, advance["bank"])
            success, error_message = bank_adapter.make_payment(advance["account_id"], advance["recipient_id"], advance["advance_amt"])

            if not success:
                logger.error(f"Payment failed for contract {contract_idx}, transaction {advance['transact_idx']}: {error_message}")
                raise ValueError(f"Payment failed: {error_message}")

            nonce = w3.eth.get_transaction_count(config["wallet_addr"])
            current_time = int(datetime.datetime.now().timestamp())
            payment_amt = int(Decimal(advance["advance_amt"]) * 100)

            call_function = w3_contract.functions.payAdvance(
                contract_idx, advance["transact_idx"], current_time, payment_amt, "completed"
            ).build_transaction({
                "from": config["wallet_addr"],
                "nonce": nonce,
                "gas": config["gas_limit"]
            })

            tx_receipt = load_web3.get_tx_receipt(call_function)
            if tx_receipt["status"] != 1:
                logger.error(f"Blockchain transaction failed for contract {contract_idx}, transaction {advance['transact_idx']}.")
                raise RuntimeError("Transaction failed on the blockchain.")

        except AttributeError as e:
            logger.error(f"Bank adapter error for contract {contract_idx}, transaction {advance['transact_idx']}: {str(e)}")
            raise RuntimeError(f"Bank adapter error: {str(e)}")

    return True