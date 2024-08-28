import datetime

import adapter.bank.mercury

import packages.load_web3 as load_web3
import packages.load_config as load_config

from .transaction_api import get_transactions
from .contract_api import get_contract_count, get_contract

config = load_config.load_config()

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

def from_timestamp(ts):
    return None if ts == 0 else datetime.datetime.fromtimestamp(ts)

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

def get_deposits(start_date, end_date, account_id):
    deposits = adapter.bank.mercury.get_deposits(start_date, end_date, account_id)
    return deposits