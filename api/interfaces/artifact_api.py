import logging
import requests
import boto3
from datetime import datetime

from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.core.cache import cache

from api.web3 import Web3Manager
from api.config import ConfigManager
from api.cache import CacheManager
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning
from api.interfaces.encryption_api import get_encryptor, get_decryptor
from api.utilities.formatting import from_timestamp

class ArtifactAPI(ResponseMixin):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure the class is a singleton."""
        if not cls._instance:
            cls._instance = super(ArtifactAPI, cls).__new__(cls)
        return cls._instance

    def __init__(self, registry_manager=None):
        """Initialize ArtifactAPI with necessary dependencies."""
        if not hasattr(self, "initialized"):
            self.config_manager = ConfigManager()
            self.registry_manager = registry_manager
            self.w3_manager = Web3Manager()
            self.cache_manager = CacheManager()
            self.s3_client = boto3.client('s3')
            self.logger = logging.getLogger(__name__)
            self.wallet_addr = self.config_manager.get_wallet_address("Transactor")
            self.initialized = True

            self.expiration = self.config_manager.get_presigned_url_expiration()

    def get_artifacts(self, contract_type, contract_idx, api_key=None, parties=[]):
        """Retrieve all artifacts for a contract."""
        try:
            cache_key = self.cache_manager.get_artifact_cache_key(contract_type, contract_idx)
            cached_artifacts = cache.get(cache_key)
            success_message = f"Successfully retrieved artifacts for {contract_type}:{contract_idx}"

            contract_api = self.registry_manager.get_contract_api(contract_type)
            contract = contract_api.get_contract(contract_type, contract_idx).get("data")

            if cached_artifacts is not None:
                log_info(self.logger, f"Loaded artifacts for {contract_type}:{contract_idx} from cache")
                decrypted_artifacts = [
                    self._decrypt_artifact(artifact, api_key, parties)
                    for artifact in cached_artifacts
                ]
                return self._format_success(decrypted_artifacts, success_message, status.HTTP_200_OK)

            w3_contract = self.w3_manager.get_web3_contract(contract_type)
            raw_artifacts = w3_contract.functions.getArtifacts(contract['contract_idx']).call()
            log_warning(self.logger, f"Raw artifacts for contract {contract_idx}: {raw_artifacts} retrieved from chain")

            # parse the response from chain and add an encrypted presigned url
            parsed_artifacts = [
                self._build_artifact_dict(artifact, idx, contract_type, contract)
                for idx, artifact in enumerate(raw_artifacts)
            ]

            # The cache should expire at the same time a presigned url expires
            # Also only load encrypted artifacts into cache
            cache.set(cache_key, parsed_artifacts, timeout=self.expiration)

            decrypted_artifacts = [
                self._decrypt_artifact(artifact, api_key, parties)
                for artifact in parsed_artifacts
            ]

            return self._format_success(decrypted_artifacts, success_message, status.HTTP_200_OK)

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
            cache_key = self.cache_manager.get_artifact_cache_key(contract_type, contract_idx)
            cache.delete(cache_key)

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

            cache_key = self.cache_manager.get_artifact_cache_key(contract_type, contract_idx)
            cache.delete(cache_key)

            success_message = f"Artifacts delete for {contract_type}:{contract_idx}"
            return self._format_success({"count": processed_count}, success_message, status.HTTP_204_NO_CONTENT)

        except ValidationError as e:
            error_message = f"Data error deleting artifacts for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Exceptions deleting artifacts for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def generate_presigned_url(self, s3_bucket, s3_object_key, s3_version_id=None):
        """Generate a presigned URL for accessing an S3 object."""
        try:
            params = {"Bucket": s3_bucket, "Key": s3_object_key}

            if s3_version_id:
                params["VersionId"] = s3_version_id

            presigned_url = self.s3_client.generate_presigned_url("get_object", Params=params, ExpiresIn=self.expiration)

            return self._format_success({"url": presigned_url}, "Generated presigned URL", status.HTTP_200_OK)

        except Exception as e:
            error_message = f"Failed to generate presigned URL: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _decrypt_artifact(self, artifact, api_key, parties):

        try:
            decryptor = get_decryptor(api_key, parties)
            decrypted_presigned_url = decryptor.decrypt(artifact["presigned_url"])

            decrypted_artifact = artifact.copy()
            decrypted_artifact["presigned_url"] = decrypted_presigned_url

            return decrypted_artifact

        except Exception as e:
            error_message = f"Error decrypting artifact for {artifact["contract_type"]}:{artifact["contract_idx"]}: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _build_artifact_dict(self, artifact, idx, contract_type, contract):
        """Build a dictionary representation of an artifact."""
        try:
            presigned_url_response = self.generate_presigned_url(
                artifact[3], # s3_bucket
                artifact[4], # s3_object_key
                artifact[5]  # s3_version_id
            )

            presigned_url = presigned_url_response.get("data", {}).get("url", None)
            encryptor = get_encryptor()
            encrypted_presigned_url = encryptor.encrypt(presigned_url)

            return {
                "contract_type": contract_type,
                "contract_idx": contract["contract_idx"],
                "artifact_idx": idx,
                "doc_title": artifact[0],
                "doc_type": artifact[1],
                "added_dt": from_timestamp(artifact[2]),
                "s3_bucket": artifact[3],
                "s3_object_key": artifact[4],
                "s3_version_id": artifact[5],
                "presigned_url": encrypted_presigned_url
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