import os
import json
import logging

from django.conf import settings
from api.utilities.logging import log_error, log_info, log_warning

class ConfigManager:

    def __init__(self):
        self.CONFIG_FILE_PATH = os.path.join(settings.BASE_DIR, 'api', 'managers', 'fixtures', 'config.json')
        self.logger = logging.getLogger(__name__)
        self._config_memory_cache = None

    def _load_config(self, extra=None):
        if self._config_memory_cache:
            return self._config_memory_cache
        return self._reload_config_from_file()

    def _reload_config_from_file(self):
        if not os.path.exists(self.CONFIG_FILE_PATH):
            log_error(self.logger, f"Configuration file not found: {self.CONFIG_FILE_PATH}")
            raise FileNotFoundError(f"Configuration file not found: {self.CONFIG_FILE_PATH}")

        try:
            with open(self.CONFIG_FILE_PATH, 'r') as f:
                config_list = json.load(f)
            config = {item["key"]: item["value"] for item in config_list}
            self._config_memory_cache = config
            return config
        except json.JSONDecodeError as e:
            log_error(self.logger, f"Error parsing configuration file: {e}")
            raise RuntimeError("Failed to parse config.json") from e

    def update_config(self):
        self._config_memory_cache = None
        return self._reload_config_from_file()

    def _save_config(self, config):
        try:
            config_list = [{"key": k, "value": v} for k, v in config.items()]
            with open(self.CONFIG_FILE_PATH, 'w') as f:
                json.dump(config_list, f, indent=4)
            self._config_memory_cache = config
            log_info(self.logger, "Configuration updated in file and memory cache")
        except Exception as e:
            log_error(self.logger, f"Error saving configuration: {e}")
            raise RuntimeError(f"Failed to save configuration: {e}")

    def _get_config_value(self, key, default=None):
        config = self._load_config(extra=key)
        return config.get(key, default)

    def _get_nested_config_value(self, parent_key, child_key, default=None):
        parent_value = self._get_config_value(parent_key, [])
        if not isinstance(parent_value, list):
            log_error(self.logger, f"Expected list for '{parent_key}', got {type(parent_value)}")
            return default
        for item in parent_value:
            if item.get("key") == child_key:
                return item.get("value", default)
        log_warning(self.logger, f"'{child_key}' not found in '{parent_key}'")
        return default

    def update_contract_address(self, contract_type, contract_address, contract_release):
        config = self._load_config()
        for section, value in [("contract_addr", contract_address), ("contract_release", contract_release)]:
            found = False
            for entry in config.get(section, []):
                if entry.get("key") == contract_type:
                    entry["value"] = value
                    found = True
                    log_info(self.logger, f"Updated {contract_type} {section} to {value}")
                    break
            if not found:
                raise ValueError(f"{contract_type} not found in {section}")
        self._save_config(config)


    #--- Standard Getters ---

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

    def get_contract_release(self, contract_type):
        contracts = self._get_config_value("contract_release", [])
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

    def get_token_address(self, network, token_symbol):
        """Retrieve the token address for a specific network and token symbol."""
        tokens_by_network = self._get_config_value("token_addr", [])
        
        # Find the network entry
        network_entry = next((entry for entry in tokens_by_network if entry["key"] == network), None)

        if not network_entry:
            log_warning(self.logger, f"No token configuration found for network '{network}'")
            return None

        tokens = network_entry.get("value", [])

        # Find the token entry
        token_entry = next((token for token in tokens if token["key"] == token_symbol), None)

        if token_entry:
            return token_entry.get("value")

        log_warning(self.logger, f"No address found for token '{token_symbol}' on network '{network}'")
        return None

    def get_token_addresses(self, network):
        """Retrieve the full token list (key and value) for a specific network."""
        tokens_by_network = self._get_config_value("token_addr", [])
        
        # Find the network entry
        network_entry = next((entry for entry in tokens_by_network if entry["key"] == network), None)

        if not network_entry:
            log_warning(self.logger, f"No token configuration found for network '{network}'")
            return []

        return network_entry.get("value", [])

    def get_all_token_addresses(self):
        """Returns the full list of token addresses for all networks."""
        return self._get_config_value("token_addr", [])

    def get_token_list(self, network):
        """Retrieve a list of token symbols for a specific network."""
        tokens_by_network = self._get_config_value("token_addr", [])
        
        # Find the network entry
        network_entry = next((entry for entry in tokens_by_network if entry["key"] == network), None)

        if not network_entry:
            log_warning(self.logger, f"No token configuration found for network '{network}'")
            return []

        tokens = network_entry.get("value", [])
        
        return [token["key"] for token in tokens if "key" in token]

    def get_s3_bucket(self):
        return self._get_config_value("s3_bucket")

    def get_contact_email_list(self):
        return self._get_config_value("contact_email_list", [])

    def get_presigned_url_expiration(self):
        return self._get_config_value("presigned_url_expiration", 3600)

    def get_listen_sleep_time(self):
        return self._get_config_value("listen_sleep_time", 5)

    def get_stats_sleep_time(self):
        return self._get_config_value("stats_sleep_time", 300)

    def get_network_sleep_time(self):
        return self._get_config_value("network_sleep_time", 1)