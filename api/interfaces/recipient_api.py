import logging
from api.managers import Web3Manager, ConfigManager
from api.adapters.bank import MercuryAdapter

from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.mixins import ValidationMixin, AdapterMixin, InterfaceResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning

class RecipientAPI(ValidationMixin, AdapterMixin, InterfaceResponseMixin):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure that the class is a singleton."""
        if not cls._instance:
            cls._instance = super(RecipientAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize the RecipientAPI class with configurations and logger."""
        if not hasattr(self, "initialized"):
            self.config_manager = ConfigManager()
            self.config = self.config_manager.load_config()
            self.w3_manager = Web3Manager()
            self.mercury_adapter = MercuryAdapter()

            self.logger = logging.getLogger(__name__)
            self.initialized = True  # Mark this instance as initialized

    def get_recipients(self, bank):
        try:
            adapter = self._get_bank_adapter(bank)
            recipients = adapter.get_recipients()

            success_message = f"Successfully retrieved {len(recipients)} recipients for bank {bank}"
            return self._format_success(recipients, success_message, status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Validation error retrieving recipients for bank {bank} : {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error retrieving recipients for bank '{bank}': {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)
