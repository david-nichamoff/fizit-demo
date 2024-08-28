import datetime

import adapter.bank.mercury

from decimal import Decimal

import packages.load_web3 as load_web3
import packages.load_config as load_config

from .transaction_api import get_transactions
from .contract_api import get_contract

config = load_config.load_config()

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

def from_timestamp(ts):
    return None if ts == 0 else datetime.datetime.fromtimestamp(ts)

def get_advances(contract_idx):
    advances = []
    transactions = get_transactions(contract_idx) 
    contract = get_contract(contract_idx)

    for transact in transactions:
        if transact["advance_pay_amt"] == "0.00":
            if Decimal(transact["advance_amt"]) > Decimal(0.00):
                advance_dict = {}
                advance_dict["contract_idx"] = contract["contract_idx"]
                advance_dict["transact_idx"] = transact["transact_idx"]
                advance_dict["bank"] = contract["funding_instr"]["bank"]
                advance_dict["account_id"] = contract["funding_instr"]["account_id"]
                advance_dict["recipient_id"] = contract["funding_instr"]["recipient_id"]
                advance_dict["advance_amt"] = transact["advance_amt"]
                advances.append(advance_dict)

    return advances

def add_advances(contract_idx, advances):
    contract = get_contract(contract_idx)

    for advance in advances:
        try:
            bank_adapter = getattr(adapter.bank, advance["bank"])
            success, error_message = bank_adapter.make_payment(advance["account_id"], advance["recipient_id"], advance["advance_amt"])

            if not success:
                return False

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
                return False

        except AttributeError:
            return False

    return True