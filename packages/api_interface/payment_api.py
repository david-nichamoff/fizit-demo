import datetime

import adapter.bank.mercury

import packages.load_web3 as load_web3
import packages.load_config as load_config

from .transaction_api import get_contract_transactions
from .contract_api import get_contract_count, get_contract

config = load_config.load_config()

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

def from_timestamp(ts):
    return None if ts == 0 else datetime.datetime.fromtimestamp(ts)

def pay_advance(account_id):
    transact_amt = 0

    for contract_idx in range(get_contract_count()):
        contract = get_contract(contract_idx)

        if contract["funding_instr"]["account_id"] == account_id:
            transactions = get_contract_transactions(contract_idx) 

        for transact_idx in range(len(transactions)):
            if not transactions[transact_idx]["advance_pay_amt"]:
                # transaction has not been paid 
                transact_amt += transactions[transact_idx]["advance_amt"]

        if transact_amt > 0:
            recipient_id = contract["funding_instr"]["recipient_id"]
            success, error_message = adapter.bank.mercury.make_payment(account_id, recipient_id, transact_amt)

            if success:
                for transact_idx in range(len(transactions)):
                    transaction = transactions[transact_idx]
                    if not transaction["advance_pay_amt"]:
                        nonce = w3.eth.get_transaction_count(config["wallet_addr"])
                        current_time = int(datetime.datetime.now().timestamp())
                        payment_amt =  int(transaction["advance_amt"] * 100)
                        call_function = w3_contract.functions.payAdvance(contract_idx, transact_idx, current_time, payment_amt, "completed").build_transaction \
                            ({"from":config["wallet_addr"],"nonce":nonce,"gas":config["gas_limit"]})
                        tx_receipt = load_web3.get_tx_receipt(call_function)
                        if tx_receipt["status"] != 1: return False
            else:
                print(f"Payment failed: {error_message}")
                return False

    return True

def pay_residual(contract_idx, contract, settlements):
    for settle_idx in range(len(settlements)):
        settlement = settlements[settle_idx]
        if settlement["residual_exp_amt"] > 0 and not settlement["residual_pay_dt"]:

            if contract["funding_instr"]["bank"] == "mercury":
                recipient_id = contract["funding_instr"]["recipient_id"]
                account_id = contract["funding_instr"]["account_id"]
                response = adapter.bank.mercury.make_payment(account_id, recipient_id, settlement["residual_exp_amt"])

            if response:
                nonce = w3.eth.get_transaction_count(config["wallet_addr"])
                call_function = w3_contract.functions.payResidual(contract_idx, settle_idx, datetime.datetime.now(), settlement["residual_exp_amt"], "completed").build_transaction \
                    ({"from":config["wallet_addr"],"nonce":nonce,"gas":config["gas_limit"]})
                signed_tx = w3.eth.account.sign_transaction(call_function, private_key=config["wallet_key"])
                send_tx = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                tx_receipt = w3.eth.wait_for_transaction_receipt(send_tx)
                if tx_receipt['status'] != 1: return False
            else:
                return False

    return True

def post_settlement(contract_idx, settle_idx, deposit_id, dispute_reason):
    deposit = adapter.bank.mercury.get_deposit(contract_idx, deposit_id)
    formatted_date = datetime.datetime.strptime(deposit["date"],"%Y-%m-%dT%H:%M:%S.%fZ")
    unix_timestamp = int(datetime.datetime.timestamp(formatted_date))

    nonce = w3.eth.get_transaction_count(config["wallet_addr"])
    call_function = w3_contract.functions.paySettlement(contract_idx, settle_idx, unix_timestamp, deposit['amount'] * 100, 
        'completed', dispute_reason).build_transaction({"from":config["wallet_addr"],"nonce":nonce,"gas":config["gas_limit"]})
    signed_tx = w3.eth.account.sign_transaction(call_function, private_key=config["wallet_key"])
    send_tx = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(send_tx)
    if tx_receipt['status'] != 1: return False