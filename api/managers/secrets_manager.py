import boto3
import json
import os
import logging
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SecretsManager:
    _instance = None
    _secrets_cache = None  # Static variable to store cached secrets
    _cache_timestamp = None  # Timestamp when the cache was last updated
    _cache_duration = timedelta(minutes=30)  # Cache duration (e.g., 30 minutes)

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SecretsManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, region_name="us-east-1"):
        self.region_name = region_name

    def load_keys(self):
        # Check if cache is valid or needs to be refreshed
        if self._is_cache_valid():
            logger.info("Returning cached secrets.")
            return SecretsManager._secrets_cache

        # Fetch secrets from AWS Secrets Manager
        fizit_env = os.environ.get('FIZIT_ENV')
        if not fizit_env:
            raise EnvironmentError("The FIZIT_ENV environment variable must be set to 'dev', 'test', or 'main'.")

        secret_prefix = {'dev': 'devnet', 'test': 'testnet', 'main': 'mainnet'}.get(fizit_env)
        if not secret_prefix:
            raise ValueError("FIZIT_ENV must be 'dev', 'test', or 'main'.")

        secrets_to_load = [f"{secret_prefix}/rotating-keys", f"{secret_prefix}/static-keys", f"{secret_prefix}/partner-keys"]
        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager', region_name=self.region_name)

        secrets = {}

        for secret_name in secrets_to_load:
            try:
                logger.info(f"Fetching secret value for {secret_name} from AWS Secrets Manager")
                get_secret_value_response = client.get_secret_value(SecretId=secret_name)

                if 'SecretString' in get_secret_value_response:
                    loaded_secrets = json.loads(get_secret_value_response['SecretString'])
                    secrets.update(loaded_secrets)
                    logger.info(f"Successfully loaded secrets for {secret_name}")
                else:
                    logger.warning(f"No SecretString found in the response for {secret_name}")

            except ClientError as e:
                logger.error(f"Error fetching secrets from AWS Secrets Manager: {e}")
                # Invalidate cache if there's a problem with the secrets
                self._invalidate_cache()
                raise

        # Cache the loaded secrets and update the timestamp
        SecretsManager._secrets_cache = secrets
        SecretsManager._cache_timestamp = datetime.now()
        logger.info("Secrets loaded and cached successfully.")
        return secrets

    def _is_cache_valid(self):
        """
        Check if the cache is still valid based on the cache duration.
        """
        if SecretsManager._secrets_cache is None:
            return False

        if SecretsManager._cache_timestamp is None:
            return False

        # Check if the cache has expired based on the set duration
        if datetime.now() - SecretsManager._cache_timestamp > SecretsManager._cache_duration:
            logger.info("Cache has expired. Secrets need to be refreshed.")
            return False

        return True

    def _invalidate_cache(self):
        """
        Invalidate the cached secrets by clearing the cache and resetting the timestamp.
        """
        SecretsManager._secrets_cache = None
        SecretsManager._cache_timestamp = None
        logger.info("Cache invalidated.")