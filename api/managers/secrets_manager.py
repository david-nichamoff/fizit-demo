import boto3
import json
import os
import logging
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

from api.utilities.logging import log_error, log_info, log_warning

class SecretsManager():
    _instance = None
    _secrets_cache = None
    _cache_timestamp = None
    _cache_duration = timedelta(hours=6)

    def __new__(cls, *args, **kwargs):
        """Ensure the class is a singleton."""
        if not cls._instance:
            cls._instance = super(SecretsManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, region_name="us-east-1"):
        """Initialize the SecretsManager with AWS region and logger."""
        if not hasattr(self, "_initialized"):
            self.region_name = region_name
            self._initialized = True
            self.logger = logging.getLogger(__name__)

    def load_keys(self):
        """Load secrets from AWS Secrets Manager, with caching."""
        if self._is_cache_valid():
            return self._secrets_cache

        secrets = {}
        fizit_env = os.getenv("FIZIT_ENV")

        if not fizit_env or fizit_env not in {"dev", "test", "main"}:
            raise EnvironmentError("FIZIT_ENV must be set to 'dev', 'test', or 'main'.")

        secret_prefix = {"dev": "devnet", "test": "testnet", "main": "mainnet"}[fizit_env]
        client = boto3.client(service_name="secretsmanager", region_name=self.region_name)

        try:
            # Load individual secrets
            secrets["FIZIT_MASTER_KEY"] = self._fetch_secret(client, f"{secret_prefix}/master-key", "api_key")
            secrets["aes_key"] = self._fetch_secret(client, f"{secret_prefix}/contract-key", "aes_key")
            secrets.update(self._fetch_secret(client, f"{secret_prefix}/static-keys"))
            secrets.update(self._fetch_secret(client, f"{secret_prefix}/cs-keys"))
            secrets.update(self._fetch_partner_api_keys(client, secret_prefix))

            self._secrets_cache = secrets
            self._cache_timestamp = datetime.now()
            return secrets

        except ClientError as e:
            log_error(self.logger, f"Error fetching secrets: {e}")
            self._invalidate_cache()
            raise RuntimeError("Failed to load secrets.") from e

    def _fetch_secret(self, client, secret_name, key=None):
        """Fetch a single secret from AWS Secrets Manager."""
        try:
            response = client.get_secret_value(SecretId=secret_name)
            secret_string = response.get("SecretString")
            if not secret_string:
                log_warning(self.logger, f"No SecretString found for {secret_name}.")
                return {}

            secret_data = json.loads(secret_string)
            return secret_data[key] if key else secret_data

        except ClientError as e:
            log_error(self.logger, f"Error fetching secret '{secret_name}': {e}")
            raise

    def _fetch_partner_api_keys(self, client, secret_prefix):
        """Fetch partner API keys from AWS Secrets Manager."""
        partner_keys = {}

        try:
            response = client.list_secrets(Filters=[{"Key": "name", "Values": [f"{secret_prefix}/api-key-"]}])
            for secret in response.get("SecretList", []):
                secret_name = secret["Name"]
                partner_code = secret_name.split(f"{secret_prefix}/api-key-")[-1]
                partner_keys[partner_code] = self._fetch_secret(client, secret_name, "api_key")

        except ClientError as e:
            log_error(self.logger, f"Error listing partner API keys: {e}")
            raise

        return partner_keys

    def _is_cache_valid(self):
        """Check if the cached secrets are still valid."""
        if not self._secrets_cache or not self._cache_timestamp:
            return False
        return datetime.now() - self._cache_timestamp <= self._cache_duration

    def _invalidate_cache(self):
        """Invalidate the cached secrets."""
        self._secrets_cache = None
        self._cache_timestamp = None
        log_warning(self.logger, "Secrets cache invalidated.")