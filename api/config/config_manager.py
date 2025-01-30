import os
import json
import logging
from django.conf import settings

from api.utilities.logging import log_error, log_info, log_warning

class ConfigManager:
    """Configuration Manager for loading environment-specific settings."""
    
    _instance = None
    _config_cache = None

    def __new__(cls, *args, **kwargs):
        """Ensure Singleton instance for ConfigManager."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize ConfigManager with lazy loading for configurations."""
        if not hasattr(self, 'initialized'):
            self.CONFIG_FILE_PATH = os.path.join(settings.BASE_DIR, 'api', 'config', 'config.json')
            self._config_cache = None  # Cache for loaded configurations
            self.initialized = True
            self.logger = logging.getLogger(__name__)

    def _load_config(self):
        """Load configuration from `config.json`, converting the list to a dictionary."""
        if self._config_cache is not None:
            return self._config_cache  # Return cached config

        if not os.path.exists(self.CONFIG_FILE_PATH):
            log_error(self.logger, f"Configuration file not found: {self.CONFIG_FILE_PATH}")
            raise FileNotFoundError(f"Configuration file not found: {self.CONFIG_FILE_PATH}")

        try:
            with open(self.CONFIG_FILE_PATH, 'r') as config_file:
                config_list = json.load(config_file)

            # Convert list of {"key": <key>, "value": <value>} into a dictionary
            self._config_cache = {item["key"]: item["value"] for item in config_list}
            
            log_info(self.logger, "Configuration loaded successfully")
            return self._config_cache
        except json.JSONDecodeError as e:
            log_error(self.logger, f"Error parsing configuration file: {e}")
            raise RuntimeError("Failed to parse config.json") from e

    def _get_config_value(self, key, default=None):
        """Retrieve a specific configuration value, loading from cache if needed."""
        if self._config_cache is None:
            self._load_config()
        return self._config_cache.get(key, default)

    def _get_nested_config_value(self, parent_key, child_key, default=None):
        if self._config_cache is None:
            self._load_config()

        parent_value = self._get_config_value(parent_key, [])
        if not isinstance(parent_value, list):
            log_error(self.logger, f"Expected list for '{parent_key}', but got {type(parent_value)}")
            return default

        for item in parent_value:
            if item.get("key") == child_key:
                return item.get("value", default)

        log_warning(self.logger, f"'{child_key}' not found in configuration '{parent_key}'. Returning default.")
        return default

    def get_rpc_url(self):
        """Retrieve the correct RPC URL for the current environment."""
        return self._get_config_value("rpc")

    def get_base_url(self):
        """Retrieve the base URL for the current environment."""
        return self._get_config_value("url")

    def get_cs_url(self):
        """Retrieve the Cubist Signer (CS) service URL."""
        return self._get_nested_config_value("cs", "url")

    def get_cs_org_id(self):
        """Retrieve the Cubist Signer (CS) organization ID."""
        return self._get_nested_config_value("cs", "org_id")

    def get_wallet_address(self, wallet_name):
        """Retrieve wallet address dynamically based on the environment."""
        wallets = self._get_config_value("wallet_addr", [])

        if not isinstance(wallets, list):
            log_error(self.logger, f"Expected list for 'wallet_addr', got {type(wallets)}")
            return None

        for wallet in wallets:
            if wallet.get("key") == wallet_name:
                return wallet.get("value")

        log_warning(self.logger, f"Wallet '{wallet_name}' not found in configuration.")
        return None  # Return None if not found

    def get_party_address(self, party_code):
        """Retrieve the Ethereum address of a party."""
        parties = self._get_config_value("party_addr", [])
        for party in parties:
            if party["key"] == party_code:
                return party["value"]
        return None

    def get_party_addresses(self):
        """Retrieve a list of party Ethereum addresses."""
        return self._get_config_value("party_addr", [])

    def get_chain_id(self, network):
        """Retrieve the chain ID for the given blockchain."""
        chains = self._get_config_value("chain", [])
        for chain in chains:
            if chain["key"] == network:
                return chain["value"]
        return None

    def get_mercury_url(self):
        """Retrieve the Mercury API URL."""
        return self._get_config_value("mercury_url")

    def get_contract_address(self, contract_type):
        """Retrieve the deployed contract address dynamically."""
        contracts = self._get_config_value("contract_addr", [])
        for contract in contracts:
            if contract["key"] == contract_type:
                return contract["value"]
        return None


    def update_contract_address(self, contract_type, contract_address):
        """Update the contract address for a specific contract type and write to config.json."""
        if self._config_cache is None:
            self._load_config()

        # Find the contract_addr entry in the config
        contract_entry = next((entry for entry in self._config_cache if entry["key"] == "contract_addr"), None)

        if not contract_entry or "value" not in contract_entry:
            log_error(self.logger, "Contract addresses section not found in configuration.")
            raise ValueError("Contract addresses section not found in configuration.")

        contracts = contract_entry["value"]

        # Update the contract address if found
        for contract in contracts:
            if contract["key"] == contract_type:
                old_address = contract["value"]
                contract["value"] = contract_address
                log_info(self.logger, f"Updated {contract_type} contract address from {old_address} to {contract_address}")
                break
        else:
            # If contract_type is not found, raise an error
            log_error(self.logger, f"Contract type '{contract_type}' not found in configuration.")
            raise ValueError(f"Contract type '{contract_type}' not found in configuration.")

        # Save the updated config back to file
        self._write_config()

    def get_contract_abi(self, contract_type):
        """Retrieve the ABI for a given contract type from a fixed location."""
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
        """Retrieve ERC-20 token contract address dynamically."""
        tokens = self._get_config_value("token_addr", [])
        for token in tokens:
            if token["key"] == token_symbol:
                return token["value"]
        return None

    def get_token_addresses(self):
        """Retrieve a list of token contract addresses."""
        return self._get_config_value("token_addr", [])

    def get_s3_bucket(self):
        """Retrieve the S3 bucket name."""
        return self._get_config_value("s3_bucket")

    def get_contact_email_list(self):
        """Retrieve the list of contact emails."""
        return self._get_config_value("contact_email_list", [])

    def update_contract_address(self, contract_type, contract_address):
        """Update the contract address for a specific contract type and write to config.json."""
        if self._config_cache is None:
            self._load_config()

        # Retrieve contract addresses as a dictionary (not a list!)
        contracts = self._config_cache.get("contract_addr", {})

        if not isinstance(contracts, list):
            log_error(self.logger, "Contract addresses section is not a list in configuration.")
            raise ValueError("Contract addresses section is not a list in configuration.")

        # Update contract address if found
        for contract in contracts:
            if contract["key"] == contract_type:
                old_address = contract["value"]
                contract["value"] = contract_address
                log_info(self.logger, f"Updated {contract_type} contract address from {old_address} to {contract_address}")
                break
        else:
            log_error(self.logger, f"Contract type '{contract_type}' not found in configuration.")
            raise ValueError(f"Contract type '{contract_type}' not found in configuration.")

        # Save the updated config back to file
        self._write_config()

    def _write_config(self):
        """Write the updated configuration back to `config.json` while maintaining its original list format."""
        try:
            # Convert _config_cache (dict) back to the original list format
            config_list = [{"key": key, "value": value} for key, value in self._config_cache.items()]

            with open(self.CONFIG_FILE_PATH, 'w') as config_file:
                json.dump(config_list, config_file, indent=4)

            log_info(self.logger, f"Configuration successfully updated in {self.CONFIG_FILE_PATH}")

            # Reload the cache after writing
            self._load_config()

        except Exception as e:
            log_error(self.logger, f"Error writing to configuration file: {e}")
            raise