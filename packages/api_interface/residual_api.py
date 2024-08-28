import datetime

from decimal import Decimal

import adapter.bank.mercury

import packages.load_web3 as load_web3
import packages.load_config as load_config

from .settlement_api import get_settlements
from .contract_api import get_contract

config = load_config.load_config()

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

def from_timestamp(ts):
    return None if ts == 0 else datetime.datetime.fromtimestamp(ts)

def get_residuals(contract_idx):
    residuals = []
    settlements = get_settlements(contract_idx) 
    contract = get_contract(contract_idx)

    for settle in settlements:
        if settle["residual_pay_amt"] == "0.00":
            if Decimal(settle["residual_exp_amt"]) > Decimal(0.00):
                residual_dict = {}
                residual_dict["contract_idx"] = contract["contract_idx"]
                residual_dict["settle_idx"] = settle["settle_idx"]
                residual_dict["bank"] = contract["funding_instr"]["bank"]
                residual_dict["account_id"] = contract["funding_instr"]["account_id"]
                residual_dict["recipient_id"] = contract["funding_instr"]["recipient_id"]
                residual_dict["residual_exp_amt"] = settle["residual_exp_amt"]

                residuals.append(residual_dict)

    return residuals

def add_residuals(contract_idx, residuals):
    if not residuals:
        return True

    contract = get_contract(contract_idx)

    for residual in residuals:
        try:
            bank_adapter = getattr(adapter.bank, residuals["bank"])
            success, error_message = bank_adapter.make_payment(residual["account_id"], residual["recipient_id"], residual["advance_amt"])

            if not success:
                return False

            nonce = w3.eth.get_transaction_count(config["wallet_addr"])
            current_time = int(datetime.datetime.now().timestamp())
            payment_amt = int(residual["residual_exp_amt"] * 100)

            call_function = w3_contract.functions.payAdvance(
                contract_idx, residual["transact_idx"], current_time, payment_amt, "completed"
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