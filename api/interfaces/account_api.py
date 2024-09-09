import logging

from api.managers import ConfigManager
from api.adapters.bank import MercuryAdapter

class AccountAPI:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure that the class is a singleton."""
        if not cls._instance:
            cls._instance = super(AccountAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize the AccountAPI class with configurations and logger."""
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()

        self.mercury_adapter = MercuryAdapter()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

    def get_accounts(self, bank):
        """Get accounts based on the bank type."""
        if bank == "mercury":
            return self.mercury_adapter.get_accounts()
        else:
            error_message = f"Unsupported bank: {bank}"
            self.logger.error(error_message)
            raise ValueError(error_message)

# Usage example:
# account_api = AccountAPI()
# accounts = account_api.get_accounts("mercury")