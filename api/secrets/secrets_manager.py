import boto3
import json
import os
import logging
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

from django.core.cache import cache

from api.cache import CacheManager
from api.utilities.logging import log_error, log_info, log_warning

class SecretsManager:
    """Secrets Manager for retrieving AWS Secrets securely with caching."""
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure Singleton instance for SecretsManager."""
        if cls._instance is None:
            cls._instance = super(SecretsManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, region_name="us-east-1"):
        """Initialize SecretsManager with AWS region and logging."""
        if not hasattr(self, "_initialized"):
            self.region_name = region_name
            self._initialized = True
            self.cache_manager = CacheManager()
            self.logger = logging.getLogger(__name__)

            self.cache_key = self.cache_manager.get_secret_cache_key()

    def _load_secrets(self):
        """(Internal) Load secrets from AWS Secrets Manager with caching."""
        secrets = cache.get(self.cache_key)

        if secrets:
            log_info(self.logger, "Loaded secrets from cache.")
            return secrets

        return self._reload_secrets_from_aws()

    def _reload_secrets_from_aws(self):
        secrets = {}
        fizit_env = os.getenv("FIZIT_ENV")

        if not fizit_env or fizit_env not in {"dev", "test", "main"}:
            raise EnvironmentError("FIZIT_ENV must be set to 'dev', 'test', or 'main'.")

        secret_prefix = {"dev": "devnet", "test": "testnet", "main": "mainnet"}[fizit_env]
        client = boto3.client(service_name="secretsmanager", region_name=self.region_name)

        try:
            # Load secrets
            secrets["FIZIT_MASTER_KEY"] = self._fetch_secret(client, f"{secret_prefix}/master-key", "api_key")
            secrets["aes_key"] = self._fetch_secret(client, f"{secret_prefix}/contract-key", "aes_key")
            secrets["static_keys"] = self._fetch_secret(client, f"{secret_prefix}/static-keys")
            secrets["cs_keys"] = self._fetch_secret(client, f"{secret_prefix}/cs-keys")
            secrets["partner_keys"] = self._fetch_partner_api_keys(client, secret_prefix)

            # Store in Redis with no expiration (timeout=None)
            cache.set(self.cache_key, secrets, timeout=None)
            log_info(self.logger, "Secrets reloaded from AWS and cached in Redis.")

            return secrets

        except ClientError as e:
            log_error(self.logger, f"Error fetching secrets: {e}")
            raise RuntimeError("Failed to load secrets.") from e

    def _fetch_secret(self, client, secret_name, key=None):
        """(Internal) Fetch a single secret from AWS Secrets Manager."""
        try:
            response = client.get_secret_value(SecretId=secret_name)
            secret_string = response.get("SecretString")
            if not secret_string:
                log_error(self.logger, f"No SecretString found for {secret_name}.")
                return {}

            secret_data = json.loads(secret_string)
            return secret_data[key] if key else secret_data

        except ClientError as e:
            log_error(self.logger, f"Error fetching secret '{secret_name}': {e}")
            raise

    def _fetch_partner_api_keys(self, client, secret_prefix):
        """(Internal) Fetch partner API keys from AWS Secrets Manager."""
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
        """(Internal) Check if the cached secrets are still valid."""
        if not self._secrets_cache or not self._cache_timestamp:
            return False
        return datetime.now() - self._cache_timestamp <= self._cache_duration

    def reset_secret_cache(self):
        """Clear secrets cache and reload from AWS."""
        cache.delete(self.cache_key)
        log_info(self.logger, "Secrets cache cleared.")
        return self._reload_secrets_from_aws()

    # --- Public API Methods ---

    def get_master_key(self):
        """Retrieve the FIZIT Master Key."""
        return self._load_secrets().get("FIZIT_MASTER_KEY")

    def get_aes_key(self):
        """Retrieve the AES contract encryption key."""
        return self._load_secrets().get("aes_key")

    def _get_static_keys(self):
        """Retrieve static keys from AWS Secrets Manager."""
        return self._load_secrets().get("static_keys", {})

    def get_mercury_key(self):
        """Retrieve the mercury banking key"""
        return self._get_static_keys().get("mercury_token")

    def get_cs_role_session_token(self):
        """Retrieve Cubist (CS) signing keys."""
        return self._load_secrets().get("cs_keys", {}).get("role_session_token")

    def get_partner_api_key(self, partner_code):
        """Retrieve API key for a specific partner."""
        return self._load_secrets().get("partner_keys", {}).get(partner_code)

    def get_all_partner_keys(self):
        """Retrieve all partner API keys."""
        return self._load_secrets().get("partner_keys", {})