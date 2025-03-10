import os
import json
import logging

from django.conf import settings
from django.db import transaction
from django.core.cache import cache

from api.cache import CacheManager
from api.utilities.logging import log_error, log_info, log_warning

class ConfigManager:
    """Configuration Manager for loading environment-specific settings."""
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure Singleton instance for ConfigManager."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize ConfigManager with lazy loading for configurations."""
        if not hasattr(self, 'initialized'):
            self.CONFIG_FILE_PATH = os.path.join(settings.BASE_DIR, 'api', 'config', 'config.json')
            self.logger = logging.getLogger(__name__)
            self.cache_manager = CacheManager()
            self.initialized = True

            self.cache_key = self.cache_manager.get_config_cache_key()

    def _load_config(self):
        """Load configuration from `config.json`, converting the list to a dictionary."""
        config = cache.get(self.cache_key)

        if config:
            log_info(self.logger, "Loaded configuration from cache")
            return config

        return self._reload_config_from_file()

    def _reload_config_from_file(self):
        """Force reload configuration from the `config.json` file and update cache."""
        if not os.path.exists(self.CONFIG_FILE_PATH):
            log_error(self.logger, f"Configuration file not found: {self.CONFIG_FILE_PATH}")
            raise FileNotFoundError(f"Configuration file not found: {self.CONFIG_FILE_PATH}")

        try:
            with open(self.CONFIG_FILE_PATH, 'r') as config_file:
                config_list = json.load(config_file)

            # Convert list of {"key": <key>, "value": <value>} into a dictionary
            config = {item["key"]: item["value"] for item in config_list}

            # Store in Redis cache with no expiration
            cache.set(self.cache_key, config, timeout=None)
            log_info(self.logger, "Configuration reloaded from file and cached in Redis")

            return config

        except json.JSONDecodeError as e:
            log_error(self.logger, f"Error parsing configuration file: {e}")
            raise RuntimeError("Failed to parse config.json") from e

    def update_config(self):
        """Clear the cache and reload configuration from file."""
        cache.delete(self.cache_key)
        log_info(self.logger, "Configuration cache cleared.")
        return self._reload_config_from_file()

    def _load_config(self):
        """Load configuration from `config.json`, converting the list to a dictionary."""
        config = cache.get(self.cache_key)

        if config:
            return config

        if not os.path.exists(self.CONFIG_FILE_PATH):
            log_error(self.logger, f"Configuration file not found: {self.CONFIG_FILE_PATH}")
            raise FileNotFoundError(f"Configuration file not found: {self.CONFIG_FILE_PATH}")

        try:
            with open(self.CONFIG_FILE_PATH, 'r') as config_file:
                config_list = json.load(config_file)

            # Convert list of {"key": <key>, "value": <value>} into a dictionary
            config = {item["key"]: item["value"] for item in config_list}

            # Store in Redis cache
            cache.set(self.cache_key, config, timeout=None)
            log_info(self.logger, "Configuration loaded from file and cached in Redis")

            return config

        except json.JSONDecodeError as e:
            log_error(self.logger, f"Error parsing configuration file: {e}")
            raise RuntimeError("Failed to parse config.json") from e

    def _save_config(self, config):
        """Save the updated configuration to both Redis and `config.json`."""
        try:
            # Convert config dictionary back to list format
            config_list = [{"key": key, "value": value} for key, value in config.items()]

            with open(self.CONFIG_FILE_PATH, "w") as config_file:
                json.dump(config_list, config_file, indent=4)

            # Update Redis cache
            cache.set(self.cache_key, config, timeout=None)
            log_info(self.logger, "Configuration updated in file and Redis cache")

        except Exception as e:
            log_error(self.logger, f"Error saving configuration: {e}")
            raise RuntimeError(f"Failed to save configuration: {e}")

    def _get_config_value(self, key, default=None):
        """Retrieve a specific configuration value, loading from cache if needed."""
        config = self._load_config()
        return config.get(key, default)

    def _get_nested_config_value(self, parent_key, child_key, default=None):
        parent_value = self._get_config_value(parent_key, [])

        if not isinstance(parent_value, list):
            log_error(self.logger, f"Expected list for '{parent_key}', but got {type(parent_value)}")
            return default

        for item in parent_value:
            if item.get("key") == child_key:
                return item.get("value", default)

        log_warning(self.logger, f"'{child_key}' not found in configuration '{parent_key}'. Returning default.")
        return default

    def update_contract_address(self, contract_type, contract_address):
        """Update contract address"""
        config = self._load_config()
        contracts = config.get("contract_addr", [])

        if not isinstance(contracts, list):
            log_error(self.logger, "Contract addresses section is not a list in configuration.")
            raise ValueError("Contract addresses section is not a list in configuration.")

        # Update contract address
        updated = False
        for contract in contracts:
            if isinstance(contract, dict) and contract.get("key") == contract_type:
                old_address = contract.get("value", "N/A")
                contract["value"] = contract_address
                updated = True
                log_info(self.logger, f"Updated {contract_type} contract address from {old_address} to {contract_address}")
                break

        if not updated:
            log_error(self.logger, f"Contract type '{contract_type}' not found in configuration.")
            raise ValueError(f"Contract type '{contract_type}' not found in configuration.")

        # Save updated config
        self._save_config(config)

    ### **Standard Getters Using Redis Cache**

    def get_rpc_url(self):
        return self._get_config_value("rpc")

    def get_base_url(self):
        return self._get_config_value("url")

    def get_cs_url(self):
        return self._get_nested_config_value("cs", "url")

    def get_cs_org_id(self):
        return self._get_nested_config_value("cs", "org_id")

    def get_wallet_address(self, wallet_name):
        wallets = self._get_config_value("wallet_addr", [])
        if isinstance(wallets, list):
            for wallet in wallets:
                if wallet.get("key") == wallet_name:
                    return wallet.get("value")
        return None

    def get_party_address(self, party_code):
        parties = self._get_config_value("party_addr", [])
        for party in parties:
            if party["key"] == party_code:
                return party["value"]
        return None

    def get_party_addresses(self):
        return self._get_config_value("party_addr", [])

    def get_party_codes(self):
        party_codes = self._get_config_value("party_addr", [])
        return [party_code["key"] for party_code in party_codes if "key" in party_code]

    def get_wallet_addresses(self):
        return self._get_config_value("wallet_addr", [])

    def get_chain_id(self, network):
        chains = self._get_config_value("chain", [])
        for chain in chains:
            if chain["key"] == network:
                return chain["value"]
        return None

    def get_mercury_url(self):
        return self._get_config_value("mercury_url")

    def get_contract_address(self, contract_type):
        contracts = self._get_config_value("contract_addr", [])
        for contract in contracts:
            if contract["key"] == contract_type:
                return contract["value"]
        return None

    def get_contract_abi(self, contract_type):
        abi_path = os.path.join(settings.BASE_DIR, "api", "contract", "abi", f"{contract_type}.json")

        if not os.path.exists(abi_path):
            log_error(self.logger, f"ABI file not found: {abi_path}")
            raise FileNotFoundError(f"ABI file not found: {abi_path}")

        try:
            with open(abi_path, "r") as abi_file:
                return json.load(abi_file)
        except json.JSONDecodeError as e:
            log_error(self.logger, f"Error loading ABI JSON from {abi_path}: {e}")
            raise

    def get_token_address(self, token_symbol):
        tokens = self._get_config_value("token_addr", [])
        for token in tokens:
            if token["key"] == token_symbol:
                return token["value"]
        return None

    def get_token_addresses(self):
        return self._get_config_value("token_addr", [])

    def get_token_list(self):
        tokens = self._get_config_value("token_addr", [])
        return [token["key"] for token in tokens if "key" in token]

    def get_s3_bucket(self):
        return self._get_config_value("s3_bucket")

    def get_contact_email_list(self):
        return self._get_config_value("contact_email_list", [])

    def get_presigned_url_expiration(self):
        return self._get_config_value("presigned_url_expiration", 3600)

    def get_listen_sleep_time(self):
        return self._get_config_value("list_sleep_time", 5)

    def get_stats_sleep_time(self):
        return self._get_config_value("stats_sleep_time", 300)