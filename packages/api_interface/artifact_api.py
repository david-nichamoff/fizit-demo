import datetime
import os

import packages.load_web3 as load_web3
import packages.load_config as load_config

import adapter.artifact.numbers

from .contract_api import get_contract

config = load_config.load_config()

ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

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
        artifact_dict["artifact_idx"] = len(artifacts)
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