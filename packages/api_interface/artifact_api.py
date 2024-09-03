import datetime
import os
import logging

import packages.load_web3 as load_web3
import packages.load_config as load_config

import adapter.artifact.numbers

from .contract_api import get_contract

config = load_config.load_config()
logger = logging.getLogger(__name__)

ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

def get_artifacts(contract_idx):
    artifacts = []
    try:
        contract = get_contract(contract_idx)
        facts = w3_contract.functions.getArtifacts(contract['contract_idx']).call()

        for artifact in facts:
            artifact_dict = {
                "contract_idx": contract["contract_idx"],
                "contract_name": contract["contract_name"],
                "artifact_id": artifact["artifact_id"],
                "doc_title": artifact["doc_title"],
                "doc_type": artifact["doc_type"],
                "added_dt": artifact["added_dt"],
                "artifact_idx": len(artifacts)
            }
            artifacts.append(artifact_dict)

        sorted_artifacts = sorted(artifacts, key=lambda d: d['added_dt'], reverse=True)
        return sorted_artifacts

    except Exception as e:
        logger.error(f"Error retrieving artifacts for contract {contract_idx}: {str(e)}")
        raise RuntimeError(f"Error retrieving artifacts for contract {contract_idx}: {str(e)}") from e

def add_artifacts(contract_idx, contract_name):
    try:
        artifact_path = os.path.join(os.environ['PYTHONPATH'], '..', 'artifacts', str(contract_idx))
        artifact_files = next(os.walk(artifact_path))[2]
        current_time = int(datetime.datetime.now().timestamp())

        return adapter.artifact.numbers.add_artifacts(contract_idx, contract_name, artifact_path, artifact_files, current_time)

    except FileNotFoundError as e:
        logger.error(f"Artifact path not found for contract {contract_idx}: {artifact_path}")
        raise RuntimeError(f"Artifact path not found: {artifact_path}") from e
    except Exception as e:
        logger.error(f"Error adding artifacts for contract {contract_idx}: {str(e)}")
        raise RuntimeError(f"Error adding artifacts for contract {contract_idx}: {str(e)}") from e

def delete_artifacts(contract_idx):
    try:
        artifacts = w3_contract.functions.getArtifacts(contract_idx).call()
        return adapter.artifact.numbers.delete_artifacts(contract_idx, artifacts)

    except Exception as e:
        logger.error(f"Error deleting artifacts for contract {contract_idx}: {str(e)}")
        raise RuntimeError(f"Error deleting artifacts for contract {contract_idx}: {str(e)}") from e