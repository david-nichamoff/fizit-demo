class CacheManager:
    """Centralized registry for cache keys used in the system."""

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