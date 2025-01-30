import logging
import requests
import boto3
from datetime import datetime

from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.web3 import Web3Manager
from api.config import ConfigManager
from api.registry import RegistryManager
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning
from api.utilities.formatting import from_timestamp

class ArtifactAPI(ResponseMixin):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure the class is a singleton."""
        if not cls._instance:
            cls._instance = super(ArtifactAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize ArtifactAPI with necessary dependencies."""
        if not hasattr(self, "initialized"):
            self.config_manager = ConfigManager()
            self.registry_manager = RegistryManager()
            self.w3_manager = Web3Manager()
            self.s3_client = boto3.client('s3')
            self.logger = logging.getLogger(__name__)
            self.wallet_addr = self.config_manager.get_wallet_address("Transactor")
            self.initialized = True

    def get_artifacts(self, contract_type, contract_idx):
        """Retrieve all artifacts for a contract."""
        try:
            contract_api = self.registry_manager.get_contract_api(contract_type)
            response = contract_api.get_contract(contract_type, contract_idx)
            contract = response["data"]
            log_info(self.logger, f"Retrieved {contract_type}:{contract_idx}: {contract}")

            w3_contract = self.w3_manager.get_web3_contract(contract_type)
            raw_artifacts = w3_contract.functions.getArtifacts(contract['contract_idx']).call()
            log_info(self.logger, f"Raw artifacts for contract {contract_idx}: {raw_artifacts}")

            artifacts = [
                self._build_artifact_dict(contract_type, contract_idx, idx, artifact)
                for idx, artifact in enumerate(raw_artifacts)
            ]
            log_info(self.logger, f"Formatted artifacts for {contract_type}:{contract_idx}: {artifacts}")

            success_message = f"Retrieved artifacts for {contract_type}:{contract_idx}"
            return self._format_success(artifacts, success_message, status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Data error retrieving artifacts for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Exception retrieving artifacts for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_artifacts(self, contract_type, contract_idx, artifact_urls):
        """Add artifacts for a contract from URLs."""
        try:
            s3_bucket = self.config_manager.get_s3_bucket()
            current_time = int(datetime.now().timestamp())
            processed_count = 0

            for artifact_url in artifact_urls:
                artifact_filename = artifact_url.split("/")[-1]
                s3_object_key, version_id = self._upload_to_s3(artifact_url, s3_bucket, contract_type, contract_idx, artifact_filename)
                doc_type = self._determine_content_type(artifact_filename)
                self._record_artifact_on_blockchain(
                    contract_type, contract_idx, artifact_filename, doc_type, current_time, s3_bucket, s3_object_key, version_id
                )
                processed_count += 1

            data = {"count": processed_count}
            success_message = f"Added artifacts for {contract_type}:{contract_idx}"
            return self._format_success(data, success_message, status.HTTP_201_CREATED)

        except ValidationError as e:
            error_message = f"Data error adding artifacts for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Exception adding artifacts for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete_artifacts(self, contract_type, contract_idx):

        try:
            artifacts = self.get_artifacts(contract_type, contract_idx)["data"]
            processed_count = 0

            for artifact in artifacts:
                self._delete_from_s3(artifact["s3_bucket"], artifact["s3_object_key"], artifact.get("s3_version_id"))
                processed_count += 1

            w3_contract = self.w3_manager.get_web3_contract(contract_type)
            transaction = w3_contract.functions.deleteArtifacts(contract_idx).build_transaction()
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_type, contract_idx, "fizit")

            if tx_receipt["status"] != 1:
                raise RuntimeError("Blockchain transaction to delete artifacts failed.")

            success_message = f"Artifacts delete for {contract_type}:{contract_idx}"
            return self._format_success({"count": processed_count}, success_message, status.HTTP_204_NO_CONTENT)

        except ValidationError as e:
            error_message = f"Data error deleting artifacts for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Exceptions deleting artifacts for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def generate_presigned_url(self, s3_bucket, s3_object_key, s3_version_id=None, expiration=3600):
        """Generate a presigned URL for accessing an S3 object."""
        try:
            params = {"Bucket": s3_bucket, "Key": s3_object_key}
            if s3_version_id:
                params["VersionId"] = s3_version_id
            presigned_url = self.s3_client.generate_presigned_url("get_object", Params=params, ExpiresIn=expiration)

            return self._format_success({"url": presigned_url}, "Generated presigned URL", status.HTTP_200_OK)

        except Exception as e:
            error_message = f"Failed to generate presigned URL: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _build_artifact_dict(self, contract_type, contract_idx, artifact_idx, artifact):
        """Build a dictionary representation of an artifact."""
        try:
            return {
                "contract_type": contract_type,
                "contract_idx": contract_idx,
                "artifact_idx": artifact_idx,
                "doc_title": artifact[0],
                "doc_type": artifact[1],
                "added_dt": from_timestamp(artifact[2]),
                "s3_bucket": artifact[3],
                "s3_object_key": artifact[4],
                "s3_version_id": artifact[5],
            }

        except Exception as e:
            error_message = f"Error building artifact dictionary: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _upload_to_s3(self, artifact_url, bucket, contract_type, contract_idx, artifact_filename):
        """Download and upload an artifact to S3."""
        try:
            response = requests.get(artifact_url)
            response.raise_for_status()
            object_key = f"{contract_type}_{contract_idx}/{artifact_filename}"
            self.s3_client.put_object(Body=response.content, Bucket=bucket, Key=object_key)
            head_response = self.s3_client.head_object(Bucket=bucket, Key=object_key)
            version_id = head_response.get("VersionId", "")
            return object_key, version_id

        except Exception as e:
            error_message = f"Error uploading artifact to s3: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _record_artifact_on_blockchain(self, contract_type, contract_idx, doc_title, doc_type, added_dt, bucket, object_key, version_id):
        """Record an artifact on the blockchain."""
        try:
            w3_contract = self.w3_manager.get_web3_contract(contract_type)
            transaction = w3_contract.functions.addArtifact(
                contract_idx, doc_title, doc_type, added_dt, bucket, object_key, version_id
            ).build_transaction()
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_type, contract_idx, "fizit")
            if tx_receipt["status"] != 1:
                raise RuntimeError("Blockchain transaction failed.")

        except Exception as e:
            error_message = f"Error recording artifact {doc_title} on blockchain: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _delete_from_s3(self, bucket, object_key, version_id=None):
        """Delete an artifact from S3."""
        try:
            params = {"Bucket": bucket, "Key": object_key}
            if version_id:
                params["VersionId"] = version_id
            self.s3_client.delete_object(**params)

        except Exception as e:
            error_message = f"Failed to delete S3 object {object_key}: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _determine_content_type(self, filename):
        """Determine the content type based on the file extension."""
        return "application/pdf" if filename.endswith(".pdf") else "application/octet-stream"