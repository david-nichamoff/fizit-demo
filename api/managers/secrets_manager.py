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
    _cache_duration = timedelta(minutes=360)  # Cache duration (e.g., 6 hours)

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SecretsManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, region_name="us-east-1"):
        self.region_name = region_name

    def load_keys(self):
        # Check if cache is valid or needs to be refreshed
        if self._is_cache_valid():
            return SecretsManager._secrets_cache

        # Fetch secrets from AWS Secrets Manager
        fizit_env = os.environ.get('FIZIT_ENV')
        if not fizit_env:
            raise EnvironmentError("The FIZIT_ENV environment variable must be set to 'dev', 'test', or 'main'.")

        secret_prefix = {'dev': 'devnet', 'test': 'testnet', 'main': 'mainnet'}.get(fizit_env)
        if not secret_prefix:
            raise ValueError("FIZIT_ENV must be 'dev', 'test', or 'main'.")

        # Initialize Boto3 session and client
        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager', region_name=self.region_name)

        secrets = {}

        # Load the FIZIT_MASTER_KEY
        master_key_name = f"{secret_prefix}/master-key"
        try:
            get_secret_value_response = client.get_secret_value(SecretId=master_key_name)

            if 'SecretString' in get_secret_value_response:
                loaded_master_key = json.loads(get_secret_value_response['SecretString'])
                secrets['FIZIT_MASTER_KEY'] = loaded_master_key.get('api_key')
            else:
                logger.warning(f"No SecretString found in the response for {master_key_name}")

        except ClientError as e:
            logger.error(f"Error fetching FIZIT_MASTER_KEY from AWS Secrets Manager: {e}")
            self._invalidate_cache()
            raise

        # Load the AES key from {secret_prefix}/contract-key
        aes_key_name = f"{secret_prefix}/contract-key"
        try:
            get_aes_key_response = client.get_secret_value(SecretId=aes_key_name)

            if 'SecretString' in get_aes_key_response:
                aes_key_data = json.loads(get_aes_key_response['SecretString'])
                secrets['aes_key'] = aes_key_data.get('aes_key')
            else:
                logger.warning(f"No SecretString found in the response for {aes_key_name}")

        except ClientError as e:
            logger.error(f"Error fetching AES key from AWS Secrets Manager: {e}")
            self._invalidate_cache()
            raise

        # Load all keys from {secret_prefix}/static-keys
        static_keys_name = f"{secret_prefix}/static-keys"
        try:
            get_static_keys_response = client.get_secret_value(SecretId=static_keys_name)

            if 'SecretString' in get_static_keys_response:
                static_keys = json.loads(get_static_keys_response['SecretString'])
                secrets.update(static_keys)  # Add all key-value pairs to the secrets dictionary
            else:
                logger.warning(f"No SecretString found in the response for {static_keys_name}")

        except ClientError as e:
            logger.error(f"Error fetching static keys from AWS Secrets Manager: {e}")
            self._invalidate_cache()
            raise

        # Load all keys from {secret_prefix}/cs-keys
        cs_keys_name = f"{secret_prefix}/cs-keys"
        try:
            get_cs_keys_response = client.get_secret_value(SecretId=cs_keys_name)

            if 'SecretString' in get_cs_keys_response:
                cs_keys = json.loads(get_cs_keys_response['SecretString'])
                secrets.update(cs_keys)  # Add all key-value pairs to the secrets dictionary
            else:
                logger.warning(f"No SecretString found in the response for {cs_keys_name}")

        except ClientError as e:
            logger.error(f"Error fetching cs keys from AWS Secrets Manager: {e}")
            self._invalidate_cache()
            raise

        # Load the partner API keys by searching for secrets that match the pattern {secret_prefix}/api-key-{partner}
        try:
            list_secrets_response = client.list_secrets(Filters=[
                {'Key': 'name', 'Values': [f"{secret_prefix}/api-key-"]}
            ])

            for secret in list_secrets_response.get('SecretList', []):
                secret_name = secret['Name']
                partner_code = secret_name.split(f"{secret_prefix}/api-key-")[-1]  # Extract the partner code

                try:
                    get_secret_value_response = client.get_secret_value(SecretId=secret_name)

                    if 'SecretString' in get_secret_value_response:
                        loaded_partner_key = json.loads(get_secret_value_response['SecretString'])
                        secrets[partner_code] = loaded_partner_key.get('api_key')
                    else:
                        logger.warning(f"No SecretString found in the response for {secret_name}")

                except ClientError as e:
                    logger.error(f"Error fetching API key for {partner_code} from AWS Secrets Manager: {e}")
                    self._invalidate_cache()
                    raise

        except ClientError as e:
            logger.error(f"Error listing partner API keys from AWS Secrets Manager: {e}")
            self._invalidate_cache()
            raise

        # Cache the loaded secrets and update the timestamp
        SecretsManager._secrets_cache = secrets
        SecretsManager._cache_timestamp = datetime.now()
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
            return False

        return True

    def _invalidate_cache(self):
        """
        Invalidate the cached secrets by clearing the cache and resetting the timestamp.
        """
        SecretsManager._secrets_cache = None
        SecretsManager._cache_timestamp = None
        logger.warning("Cache invalidated.")