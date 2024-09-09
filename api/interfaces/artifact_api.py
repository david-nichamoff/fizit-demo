import datetime
import os
import logging

from api.managers import Web3Manager, ConfigManager
from api.interfaces import ContractAPI

class ArtifactAPI:
    _instance = None
    ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

    def __new__(cls, *args, **kwargs):
        """Ensure that the class is a singleton."""
        if not cls._instance:
            cls._instance = super(ArtifactAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.w3_manager = Web3Manager()
        self.w3 = self.w3_manager.get_web3_instance()
        self.w3_contract = self.w3_manager.get_web3_contract()
        self.contract_api = ContractAPI()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

    def get_artifacts(self, contract_idx):
        """Retrieve artifacts for a given contract."""
        artifacts = []
        try:
            contract = self.contract_api.get_contract(contract_idx)
            facts = self.w3_contract.functions.getArtifacts(contract['contract_idx']).call()

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
            self.logger.error(f"Error retrieving artifacts for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Error retrieving artifacts for contract {contract_idx}: {str(e)}") from e

    def add_artifacts(self, contract_idx, contract_name):
        """Add artifacts for a contract."""
        try:
            artifact_path = os.path.join(os.environ['PYTHONPATH'], '..', 'artifacts', str(contract_idx))
            artifact_files = next(os.walk(artifact_path))[2]
            current_time = int(datetime.datetime.now().timestamp())

            return artifact_adapter.add_artifacts(contract_idx, contract_name, artifact_path, artifact_files, current_time)

        except FileNotFoundError as e:
            self.logger.error(f"Artifact path not found for contract {contract_idx}: {artifact_path}")
            raise RuntimeError(f"Artifact path not found: {artifact_path}") from e
        except Exception as e:
            self.logger.error(f"Error adding artifacts for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Error adding artifacts for contract {contract_idx}: {str(e)}") from e

    def delete_artifacts(self, contract_idx):
        """Delete artifacts for a contract."""
        try:
            artifacts = self.w3_contract.functions.getArtifacts(contract_idx).call()
            return artifact_adapter.delete_artifacts(contract_idx, artifacts)

        except Exception as e:
            self.logger.error(f"Error deleting artifacts for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Error deleting artifacts for contract {contract_idx}: {str(e)}") from e

# Usage example:
# artifact_api = ArtifactAPI()
# artifacts = artifact_api.get_artifacts(contract_idx)
# artifact_api.add_artifacts(contract_idx, contract_name)
# artifact_api.delete_artifacts(contract_idx)