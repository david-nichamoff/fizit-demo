import logging
from django.core.cache import cache

from api.utilities.logging import log_info, log_warning, log_error

class CacheManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    # --- Cache Getters/Setters/Deleters ---
    
    def get(self, key, extra=None):
        try:
            value = cache.get(key)

            if value is not None:
                log_info(self.logger, f"Cache HIT: {key}", extra=extra)
            else:
                log_warning(self.logger, f"Cache MISS: {key}", extra=extra)

            return value

        except Exception as e:
            # Only if cache backend fails (e.g., Redis is down)
            log_error(self.logger, f"Cache ERROR retrieving key '{key}': {str(e)}")
            return None

    def set(self, key, value, timeout= None, extra=None):
        try:
            cache.set(key, value, timeout)
            log_info(self.logger, f"Cache SET: {key} (timeout={timeout})", extra=extra)
        except Exception as e:
            log_error(self.logger, f"Failed to set cache for key '{key}': {str(e)}", extra=extra)

    def delete(self, key, extra=None):
        try:
            cache.delete(key)
            log_info(self.logger, f"Cache DELETE: {key}", extra=extra)
        except Exception as e:
            log_error(self.logger, f"Failed to delete cache for key '{key}': {str(e)}", extra=extra)

    def clear_all(self):
        try:
            cache.clear()
            log_warning(self.logger, "Cache cleared (ALL KEYS)")
        except Exception as e:
            log_error(self.logger, f"Failed to clear all caches: {str(e)}")

    # --- Cache Key Generators (unchanged) ---

    @staticmethod
    def get_contract_count_cache_key(contract_type):
        return f"count_{contract_type}"

    @staticmethod
    def get_account_cache_key(bank):
        return f"account_{bank}"

    @staticmethod
    def get_recipient_cache_key(bank):
        return f"recipient_{bank}"

    @staticmethod
    def get_config_cache_key():
        return "config"

    @staticmethod
    def get_library_cache_key():
        return "library"

    @staticmethod
    def get_secret_cache_key():
        return "secret"

    @staticmethod
    def get_contract_abi_cache_key(contract_type):
        return f"contract_abi_{contract_type}"

    @staticmethod
    def get_contract_cache_key(contract_type, contract_idx):
        return f"contract_{contract_type}_{contract_idx}"

    @staticmethod
    def get_contract_list_cache_key(contract_type):
        return f"contract_list_{contract_type}"

    @staticmethod
    def get_transaction_cache_key(contract_type, contract_idx):
        return f"transaction_{contract_type}_{contract_idx}"

    @staticmethod
    def get_settlement_cache_key(contract_type, contract_idx):
        return f"settlement_{contract_type}_{contract_idx}"

    @staticmethod
    def get_party_cache_key(contract_type, contract_idx):
        return f"party_{contract_type}_{contract_idx}"

    @staticmethod
    def get_artifact_cache_key(contract_type, contract_idx):
        return f"artifact_{contract_type}_{contract_idx}"

    @staticmethod
    def get_stats_cache_key():
        return "stats"