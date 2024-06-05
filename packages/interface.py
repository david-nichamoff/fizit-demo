import datetime
import os

import json
from json_logic import jsonLogic

import web3_client
import env_var

import adapter.bank.mercury
import adapter.artifact.numbers
import adapter.ticketing.engage

from api.models import EngageSrc, EngageDest

env_var = env_var.get_env()
w3 = web3_client.get_web3_instance()
w3_contract = web3_client.get_web3_contract()

def from_timestamp(ts):
    return None if ts == 0 else datetime.datetime.fromtimestamp(ts)

def get_contract_count():
    return w3_contract.functions.getContractCount().call() 

def get_contract_dict(contract_idx):
    contract_dict, contract = {}, []
    contract = w3_contract.functions.getContract(contract_idx).call()
    contract_dict["extended_data"] = json.loads(contract[0].replace("'",'"'))
    contract_dict["contract_name"] = contract[1]
    contract_dict["funding_instr"] = json.loads(contract[2].replace("'",'"'))
    contract_dict["service_fee_pct"] = contract[3] / 10000
    contract_dict["service_fee_amt"] = contract[4] / 100
    contract_dict["advance_pct"] = contract[5] / 10000
    contract_dict["late_fee_pct"] = contract[6] / 10000
    contract_dict["transact_logic"] = json.loads(contract[7].replace("'",'"'))
    contract_dict["is_active"] = contract[8]
    contract_dict["contract_idx"] = contract_idx
    return contract_dict

def get_contracts(bank, account_ids):
    contracts = []
    for contract_idx in range(get_contract_count()):
        contract_dict = get_contract_dict(contract_idx)
        if (account_ids is None or contract_dict['funding_instr']['account_id'] in account_ids) and \
           (bank is None or bank == contract_dict['funding_instr']['bank']):
            contracts.append(contract_dict)

    return contracts

def get_contract(contract_idx):
    contract = get_contract_dict(contract_idx)
    return contract 

def build_contract(contract_dict):
    contract = []
    contract.append(str(contract_dict["extended_data"]))
    contract.append(contract_dict["contract_name"])
    contract.append(str(contract_dict["funding_instr"]))
    contract.append(int(contract_dict["service_fee_pct"] * 10000))
    contract.append(int(contract_dict["service_fee_amt"] * 100))
    contract.append(int(contract_dict["advance_pct"] * 10000))
    contract.append(int(contract_dict["late_fee_pct"] * 10000 ))
    contract.append(str(contract_dict["transact_logic"] ))
    contract.append(contract_dict["is_active"])
    return contract

def update_contract(contract_idx, contract_dict):
    contract = build_contract(contract_dict)
    nonce = w3.eth.get_transaction_count(env_var["wallet_addr"])
    call_function = w3_contract.functions.updateContract(contract_idx, contract).build_transaction(
        {"from":env_var["wallet_addr"],"nonce":nonce,"gas":env_var["gas_limit"]})
    tx_receipt = web3_client.get_tx_receipt(call_function)
    return True if tx_receipt["status"] == 1 else False

def add_contract(contract_dict):
    contract_idx = get_contract_count()
    contract = build_contract(contract_dict)
    nonce = w3.eth.get_transaction_count(env_var["wallet_addr"])
    call_function = w3_contract.functions.addContract(contract).build_transaction(
        {"from":env_var["wallet_addr"],"nonce":nonce,"gas":env_var["gas_limit"]})
    tx_receipt = web3_client.get_tx_receipt(call_function)
    return contract_idx if tx_receipt["status"] == 1 else False

def delete_contract(contract_idx):
    nonce = w3.eth.get_transaction_count(env_var["wallet_addr"])
    call_function = w3_contract.functions.deleteContract(contract_idx).build_transaction(
        {"from":env_var["wallet_addr"],"nonce":nonce,"gas":env_var["gas_limit"]}) 
    tx_receipt = web3_client.get_tx_receipt(call_function)
    return True if tx_receipt["status"] == 1 else False   

def get_settle_dict(settle, contract):
    settle_dict = {}
    settle_dict["extended_data"] = json.loads(settle[0].replace("'",'"'))
    settle_dict["settle_due_dt"] = from_timestamp(settle[1]) 
    settle_dict["transact_min_dt"] = from_timestamp(settle[2])
    settle_dict["transact_max_dt"] = from_timestamp(settle[3])
    settle_dict["transact_count"] = settle[4]
    settle_dict["settle_pay_dt"] = from_timestamp(settle[5])
    settle_dict["settle_exp_amt"] = settle[6] / 100
    settle_dict["settle_pay_amt"] = settle[7] / 100
    settle_dict["settle_confirm"] = settle[8]
    settle_dict["dispute_amt"] = settle[9]  / 100
    settle_dict["dispute_reason"] = settle[10]
    settle_dict["days_late"] = settle[11]
    settle_dict["late_fee_amt"] = settle[12] / 100
    settle_dict["residual_pay_dt"] = from_timestamp(settle[13]) 
    settle_dict["residual_pay_amt"] = settle[14] / 100
    settle_dict["residual_confirm"] = settle[15]
    settle_dict["residual_exp_amt"] = settle[16] / 100
    settle_dict["residual_calc_amt"] = settle[17] / 100
    settle_dict["contract_idx"] = contract['contract_idx']
    settle_dict["contract_name"] = contract['contract_name']
    settle_dict["funding_instr"] = contract['funding_instr']
    return settle_dict
    
def get_settlements(bank, account_ids):
    settlements = []
    contracts = get_contracts(bank, account_ids)

    for contract in contracts:
        settles = w3_contract.functions.getSettlements(contract['contract_idx']).call()
        for settle in settles:
            settle_dict = get_settle_dict(settle, contract)
            settlements.append(settle_dict)
    sorted_settlements = sorted(settlements, key=lambda d: d['settle_due_dt'], reverse=False)
    return sorted_settlements 

def get_contract_settlements(contract_idx):
    settlements = []
    contract = get_contract(contract_idx)
    settles = w3_contract.functions.getSettlements(contract['contract_idx']).call() 
    for settle in settles:
        settle_dict = get_settle_dict(settle, contract)
        settlements.append(settle_dict)
    sorted_settlements = sorted(settlements, key=lambda d: d['settle_due_dt'], reverse=False)
    return sorted_settlements 

def add_settlements(contract_idx, settlements):
    for settlement in settlements:
        due_dt = int(datetime.datetime.combine(settlement["settle_due_dt"], datetime.time.min).timestamp())
        min_dt = int(datetime.datetime.combine(settlement["transact_min_dt"], datetime.time.min).timestamp())
        max_dt = int(datetime.datetime.combine(settlement["transact_max_dt"], datetime.time.min).timestamp())
        extended_data = str(settlement["extended_data"])
        nonce = w3.eth.get_transaction_count(env_var["wallet_addr"])
        call_function = w3_contract.functions.addSettlement(contract_idx, extended_data, due_dt, min_dt, max_dt).build_transaction(
            {"from":env_var["wallet_addr"],"nonce":nonce,"gas":env_var["gas_limit"]}) 
        tx_receipt = web3_client.get_tx_receipt(call_function)
        if tx_receipt["status"] != 1: return False
    return True

def delete_settlements(contract_idx):
    nonce = w3.eth.get_transaction_count(env_var["wallet_addr"])
    call_function = w3_contract.functions.deleteSettlements(contract_idx).build_transaction(
        {"from":env_var["wallet_addr"],"nonce":nonce,"gas":env_var["gas_limit"]}) 
    tx_receipt = web3_client.get_tx_receipt(call_function)
    return True if tx_receipt["status"] == 1 else False   

def get_transact_dict(transact, contract):
    transact_dict = {}
    transact_dict["extended_data"] = json.loads(transact[0].replace("'",'"'))
    transact_dict["transact_dt"] = from_timestamp(transact[1])
    transact_dict["transact_amt"] = transact[2] / 100
    transact_dict["advance_amt"] = transact[3] / 100
    transact_dict["transact_data"] = json.loads(transact[4].replace("'",'"'))
    transact_dict["advance_pay_dt"] = from_timestamp(transact[5])
    transact_dict["advance_pay_amt"] = transact[6] / 100
    transact_dict["advance_confirm"] = transact[7]
    transact_dict["contract_idx"] = contract['contract_idx']
    transact_dict["funding_instr"] = contract['funding_instr']
    return transact_dict

def get_transactions(bank, account_ids):
    transactions = []
    contracts = get_contracts(bank, account_ids)

    for contract in contracts:
        transacts = w3_contract.functions.getTransactions(contract['contract_idx']).call()
        for transact in transacts:
            transact_dict = get_transact_dict(transact, contract)
            transactions.append(transact_dict)
    sorted_transactions = sorted(transactions, key=lambda d: d['transact_dt'], reverse=True)
    return sorted_transactions 

def get_contract_transactions(contract_idx):
    transactions=[]
    contract = get_contract(contract_idx)
    transacts = w3_contract.functions.getTransactions(contract['contract_idx']).call() 
    for transact in transacts:
        transact_dict = get_transact_dict(transact, contract)
        transactions.append(transact_dict)
    sorted_transactions = sorted(transactions, key=lambda d: d['transact_dt'], reverse=True)
    return sorted_transactions 

def add_transactions(contract_idx, transact_logic, transactions):
    for transaction in transactions:
        extended_data = str(transaction["extended_data"])
        transact_dt = int(transaction["transact_dt"].timestamp())
        transact_data = transaction["transact_data"]
        nonce = w3.eth.get_transaction_count(env_var["wallet_addr"])
        transact_amt = int(jsonLogic(transact_logic,transact_data) * 100) 
        call_function = w3_contract.functions.addTransaction(contract_idx, extended_data, transact_dt, transact_amt, str(transact_data)).build_transaction(
            {"from":env_var["wallet_addr"],"nonce":nonce,"gas":env_var["gas_limit"]}) 
        tx_receipt = web3_client.get_tx_receipt(call_function)
        if tx_receipt["status"] != 1: return False
    return True

def delete_transactions(contract_idx):
    nonce = w3.eth.get_transaction_count(env_var["wallet_addr"])
    call_function = w3_contract.functions.deleteTransactions(contract_idx).build_transaction(
        {"from":env_var["wallet_addr"],"nonce":nonce,"gas":env_var["gas_limit"]}) 
    tx_receipt = web3_client.get_tx_receipt(call_function)
    return True if tx_receipt["status"] == 1 else False   

def get_contract_tickets(contract_idx, start_date, end_date):
    contract = get_contract(contract_idx)
    tickets = []

    if contract["extended_data"]["type"] == "ticket": 
        if contract["extended_data"]["provider"] == "engage":
            engage_src = EngageSrc.objects.get(src_code=contract["extended_data"]["src_code"])
            engage_dest = EngageDest.objects.get(dest_code=contract["extended_data"]["dest_code"])
            tickets = adapter.ticketing.engage.get_tickets(contract, engage_src, engage_dest, start_date, end_date)

    return tickets 

def get_contract_artifacts(contract_idx):
    artifacts = []
    contract = get_contract(contract_idx)

    facts = w3_contract.functions.getArtifacts(contract['contract_idx']).call()
    for artifact in facts:
        artifact_dict = {}
        artifact_dict["contract_idx"] = contract["contract_idx"]
        artifact_dict["contract_name"] = contract["contract_name"]
        artifact_dict["artifact_id"] = artifact["artifact_id"]
        artifact_dict["doc_title"] = artifact["doc_title"]
        artifact_dict["doc_type"] = artifact["doc_type"]
        artifact_dict["added_dt"] = artifact["added_dt"]
        artifacts.append(artifact_dict)
    sorted_artifacts = sorted(artifacts, key=lambda d: d['added_dt'], reverse=True)
    return sorted_artifacts

def add_artifacts(contract_idx, contract_name):
    artifact_path = os.environ['PYTHONPATH'] + '/../artifacts/' + str(contract_idx) + '/'
    artifact_files = next(os.walk(artifact_path))[2]
    current_time = int(datetime.datetime.now().timestamp())
    return adapter.artifact.numbers.add_artifacts(contract_idx, contract_name, artifact_path, artifact_files, current_time)

def delete_artifacts(contract_idx):
    artifacts = w3_contract.functions.getArtifacts(contract_idx).call()
    return adapter.artifact.numbers.delete_artifacts(contract_idx, artifacts)

def get_accounts(bank):
    accounts = []
    if bank == "mercury" or bank is None:  
        accounts = adapter.bank.mercury.get_accounts()
    return accounts

def get_recipients(bank):
    if bank == "mercury" or bank is None:
        recipients = adapter.bank.mercury.get_recipients()
    return recipients

def get_deposits(start_date, end_date, account_id):
    deposits = adapter.bank.mercury.get_deposits(start_date, end_date, account_id)
    return deposits

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
                        nonce = w3.eth.get_transaction_count(env_var["wallet_addr"])
                        current_time = int(datetime.datetime.now().timestamp())
                        payment_amt =  int(transaction["advance_amt"] * 100)
                        call_function = w3_contract.functions.payAdvance(contract_idx, transact_idx, current_time, payment_amt, "completed").build_transaction \
                            ({"from":env_var["wallet_addr"],"nonce":nonce,"gas":env_var["gas_limit"]})
                        tx_receipt = web3_client.get_tx_receipt(call_function)
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
                nonce = w3.eth.get_transaction_count(env_var["wallet_addr"])
                call_function = w3_contract.functions.payResidual(contract_idx, settle_idx, datetime.datetime.now(), settlement["residual_exp_amt"], "completed").build_transaction \
                    ({"from":env_var["wallet_addr"],"nonce":nonce,"gas":env_var["gas_limit"]})
                signed_tx = w3.eth.account.sign_transaction(call_function, private_key=env_var["wallet_key"])
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

    nonce = w3.eth.get_transaction_count(env_var["wallet_addr"])
    call_function = w3_contract.functions.paySettlement(contract_idx, settle_idx, unix_timestamp, deposit['amount'] * 100, 
        'completed', dispute_reason).build_transaction({"from":env_var["wallet_addr"],"nonce":nonce,"gas":env_var["gas_limit"]})
    signed_tx = w3.eth.account.sign_transaction(call_function, private_key=env_var["wallet_key"])
    send_tx = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(send_tx)
    if tx_receipt['status'] != 1: return False