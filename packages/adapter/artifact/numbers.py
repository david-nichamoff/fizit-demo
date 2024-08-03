from rest_framework import status

import os
import requests
import json

import packages.load_web3 as load_web3
import packages.load_keys as load_keys
import packages.load_config as load_config
import packages.load_abi as load_abi

keys = load_keys.load_keys()
config = load_config.load_config()
abi = load_abi.load_abi()

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

def add_artifacts(contract_idx, contract_name, artifact_path, artifact_files, current_time):
    proof_dict = { "hash" : "", "mimeType" : "", "timestamp" : "" }
    info_dict = { "provider" : "FIZIT", "name" : contract_name, "value" : str(contract_idx) }
    meta_dict = { "proof" : proof_dict, "information" : [ info_dict ] }
    header_dict = {'Authorization' : 'token ' + str(keys["numbers_key"]) }

    for artifact_file in artifact_files:
        doc_type = "PDF"  # only document type for now, consider changing later
        caption = str(contract_idx) + ": " + str(artifact_file)
        file_dict = { "asset_file" : (artifact_file, open(artifact_path + str(artifact_file),"rb"))}
        response = requests.post(config["numbers_url"] + '/', headers=header_dict, files=file_dict, data = { 'meta' : meta_dict, 'caption' : caption, 'public_access' : False})

        if response.status_code == 201: 
            artifact_id = json.loads(response.text)['id']
            nonce = w3.eth.get_transaction_count(config["wallet_addr"])
            call_function = w3_contract.functions.addArtifact(contract_idx, artifact_id, artifact_file, doc_type, current_time).build_transaction({"from":config["wallet_addr"],"nonce":nonce})
            tx_receipt = load_web3.get_tx_receipt(call_function)
            if tx_receipt["status"] != 1: return False

    return True

def delete_artifacts(contract_idx, artifacts):
    header_dict = { 'Authorization' : 'token ' + str(keys["numbers_key"]) }

    for artifact in artifacts:
        response = requests.delete(config["numbers_url"] + "/" + artifact, headers=header_dict)

    nonce = w3.eth.get_transaction_count(config["wallet_addr"])
    call_function = w3_contract.functions.deleteArtifacts(contract_idx).build_transaction({"from":config["wallet_addr"],"nonce":nonce}) 
    tx_receipt = load_web3.get_tx_receipt(call_function)
    return True if tx_receipt["status"] == 1 else False   