import logging

from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning

class AccountAPI(ResponseMixin):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one instance is created."""
        if not cls._instance:
            cls._instance = super(AccountAPI, cls).__new__(cls)
        return cls._instance

    def __init__(self, registry_manager=None):
        """Initialize the AccountAPI class with configurations and logger."""
        if not hasattr(self, "initialized"):
            # Initialize adapters
            self.registry_manager = registry_manager 
            self.logger = logging.getLogger(__name__)

            if not self.registry_manager:
                log_error(self.logger, "RegistryManager is missing in AccountAPI!")

            self.initialized = True

    def get_accounts(self, bank):
        """Retrieve accounts for the specified bank."""
        try:
            adapter = self.registry_manager.get_bank_adapter(bank)
            accounts = adapter.get_accounts()
            success_message = f"Successfully retrieved {len(accounts)} accounts for bank {bank}"
            return self._format_success(accounts, success_message, status.HTTP_200_OK)
        except Exception as e:
            error_message = f"Unexpected error retrieving accounts for bank '{bank}': {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)