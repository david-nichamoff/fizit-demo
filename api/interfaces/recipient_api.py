import logging

from api.managers import Web3Manager, ConfigManager
from api.adapters.bank import MercuryAdapter

class RecipientAPI:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure that the class is a singleton."""
        if not cls._instance:
            cls._instance = super(RecipientAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize the RecipientAPI class with configurations and logger."""
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.w3_manager = Web3Manager()
        
        self.mercury_adapter = MercuryAdapter()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

    def get_recipients(self, bank):
        """Get recipients based on the bank type."""
        if bank == "mercury":
            return self.mercury_adapter.get_recipients()
        elif bank == "token":
            return []
        else:
            error_message = f"Unsupported bank: {bank}"
            self.logger.error(error_message)
            raise ValueError(error_message)

# Usage example:
# recipient_api = RecipientAPI()
# recipients = recipient_api.get_recipients("mercury")