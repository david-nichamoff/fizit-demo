import logging
import requests
import boto3
import datetime

from datetime import timezone, datetime, time

from botocore.exceptions import ClientError
from eth_utils import to_checksum_address

from api.managers import Web3Manager, ConfigManager
from api.interfaces import ContractAPI

class ArtifactAPI:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure the class is a singleton."""
        if not cls._instance:
            cls._instance = super(ArtifactAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.w3_manager = Web3Manager()
        self.w3_contract = self.w3_manager.get_web3_contract()
        self.contract_api = ContractAPI()

        self.s3_client = boto3.client('s3')

        self.logger = logging.getLogger(__name__)
        self.initialized = True

        self.wallet_addr = self.config_manager.get_nested_config_value("wallet_addr", "Transactor")
        self.checksum_wallet_addr = to_checksum_address(self.wallet_addr)

    def from_timestamp(self, ts):
        return None if ts == 0 else datetime.fromtimestamp(ts, tz=timezone.utc)

    def get_artifacts(self, contract_idx):
        artifacts = []
        try:
            contract = self.contract_api.get_contract(contract_idx)
            facts = self.w3_contract.functions.getArtifacts(contract['contract_idx']).call()

            # Log the facts to see what is returned
            self.logger.info(f"Artifacts returned for contract {contract_idx}: {facts}")
            artifact_idx = 0

            for artifact in facts:
                artifact_dict = self.build_artifact_dict(contract_idx, artifact_idx, artifact)
                artifact_idx += 1
                artifacts.append(artifact_dict)

            sorted_artifacts = sorted(artifacts, key=lambda d: d['added_dt'], reverse=True)
            return sorted_artifacts
        except Exception as e:
            self.logger.error(f"Error retrieving artifacts for contract {contract_idx}: {str(e)}")
            raise RuntimeError("Failed to retrieve artifacts") from e

    def build_artifact_dict(self, contract_idx, artifact_idx, artifact):
        try:
            artifact_dict = {
                "contract_idx": contract_idx,
                "artifact_idx" : artifact_idx,
                "doc_title": artifact[0],
                "doc_type": artifact[1],
                "added_dt": self.from_timestamp(artifact[2]),
                "s3_bucket": artifact[3],
                "s3_object_key": artifact[4],
                "s3_version_id": artifact[5]
            }
            return artifact_dict

        except Exception as e:
            self.logger.error(f"Error building artifact dict: {str(e)}")
            raise RuntimeError(f"Failed to build artifact dictionary") from e

    def add_artifacts(self, contract_idx, artifact_urls):
        """Add artifacts for a contract from URLs."""
        try:
            # Get the contract address from the blockchain contract
            current_time = int(datetime.now().timestamp())
            s3_bucket = self.config['s3_bucket']

            for artifact_url in artifact_urls:
                try:
                    # Download the file from the URL
                    response = requests.get(artifact_url)
                    if response.status_code != 200:
                        raise RuntimeError(f"Failed to download artifact from {artifact_url}")

                    artifact_filename = artifact_url.split("/")[-1]  # Get the filename from the URL
                    # Include both contract_idx and contract_address in the S3 object key
                    s3_object_key = f"{contract_idx}/{artifact_filename}"

                    # Upload the file content to S3
                    self.s3_client.put_object(
                        Body=response.content,
                        Bucket=s3_bucket,
                        Key=s3_object_key
                    )

                    # Get the S3 version ID after upload
                    head_response = self.s3_client.head_object(Bucket=s3_bucket, Key=s3_object_key)
                    version_id = head_response.get('VersionId', '')

                    # Determine content type based on file extension (e.g., .pdf -> application/pdf)
                    if artifact_filename.endswith('.pdf'):
                        content_type = 'application/pdf'
                    else:
                        content_type = response.headers.get('Content-Type', 'application/octet-stream')

                    # Build the transaction using the contract address and contract_idx
                    nonce = self.w3_manager.get_nonce(self.checksum_wallet_addr)

                    # Build the transaction
                    transaction = self.w3_contract.functions.addArtifact(
                        contract_idx,
                        artifact_filename,  # doc_title
                        content_type,       # doc_type
                        current_time, 
                        s3_bucket, 
                        s3_object_key, 
                        version_id
                    ).build_transaction({
                        "from": self.checksum_wallet_addr,
                        "nonce": nonce
                    })

                    tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr)

                    # Check the transaction status
                    if tx_receipt['status'] != 1:
                        raise RuntimeError(f"Transaction failed for artifact {artifact_filename} in contract {contract_idx}")

                    self.logger.info(f"Artifact {artifact_filename} uploaded from URL and added to contract {contract_idx}.")

                except requests.RequestException as e:
                    self.logger.error(f"Error downloading artifact from {artifact_url}: {str(e)}")
                    raise RuntimeError(f"Error downloading artifact from {artifact_url}: {str(e)}") from e
                except ClientError as e:
                    self.logger.error(f"Error uploading artifact {artifact_filename} to S3: {str(e)}")
                    raise RuntimeError(f"Error uploading artifact {artifact_filename} to S3: {str(e)}") from e

            return {"message": "Artifacts uploaded from URLs and added successfully"}

        except Exception as e:
            self.logger.error(f"Error adding artifacts for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Error adding artifacts for contract {contract_idx}: {str(e)}") from e

    def delete_artifacts(self, contract_idx):
        try:
            # Retrieve all artifacts for the contract before deleting them from the blockchain
            artifacts = self.get_artifacts(contract_idx)
            s3_bucket = self.config['s3_bucket']

            # Delete each artifact from S3
            for artifact in artifacts:
                try:
                    delete_params = {
                        'Bucket': s3_bucket,
                        'Key': artifact['s3_object_key']  # Use the correct key from the artifact dictionary
                    }

                    # Only include VersionId if it's present
                    if artifact.get('s3_version_id'):
                        delete_params['VersionId'] = artifact['s3_version_id']

                    # Delete the artifact from S3
                    self.s3_client.delete_object(**delete_params)
                    self.logger.info(f"Deleted artifact from S3 (Key: {artifact['s3_object_key']}, VersionId: {artifact.get('s3_version_id')}).")

                except ClientError as e:
                    self.logger.error(f"Error deleting artifact from S3: {str(e)}")
                    raise RuntimeError(f"Error deleting artifact from S3: {str(e)}") from e

            # Now delete the artifacts from the blockchain
            nonce = self.w3_manager.get_nonce(self.checksum_wallet_addr)

            # Build the transaction to delete all artifacts on-chain for the contract
            transaction = self.w3_contract.functions.deleteArtifacts(contract_idx).build_transaction({
                "from": self.checksum_wallet_addr,
                "nonce": nonce
            })

            # Send the transaction
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr)

            if tx_receipt["status"] != 1:
                raise RuntimeError(f"Failed to delete artifacts on blockchain. Transaction status: {tx_receipt['status']}")

            self.logger.info(f"Successfully deleted artifacts from both blockchain and S3 for contract {contract_idx}.")
            return {"message": f"Artifacts deleted successfully for contract {contract_idx}"}

        except Exception as e:
            self.logger.error(f"Error deleting artifacts for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to delete artifacts for contract {contract_idx}") from e
           
    def import_artifacts(self, contract_idx, artifacts):
        try:
            for artifact in artifacts:
                added_dt = int(datetime.fromisoformat(artifact["added_dt"]).timestamp())

                artifact_struct = (
                    artifact["doc_title"],
                    artifact["doc_type"],
                    added_dt, 
                    artifact["s3_bucket"],
                    artifact["s3_object_key"],
                    artifact["s3_version_id"]
                )

                self.logger.info(f"Importing artifact {artifact['doc_title']} to contract {contract_idx}")

                # Build the transaction
                nonce = self.w3_manager.get_nonce(self.checksum_wallet_addr)
                transaction = self.w3_contract.functions.importArtifact(
                    contract_idx, artifact_struct
                ).build_transaction({
                    "from": self.checksum_wallet_addr,
                    "nonce": nonce
                })

                # Send the transaction
                tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr)

                if tx_receipt["status"] != 1:
                    raise RuntimeError(f"Failed to import artifact {artifact['doc_title']} to contract {contract_idx}")

            return True

        except Exception as e:
            self.logger.error(f"Error importing artifacts to contract {contract_idx}: {str(e)}")
            raise 