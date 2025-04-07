import logging

from rest_framework import status

from api.managers.app_context import AppContext
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning

class AccountAPI(ResponseMixin):

    def __init__(self, context: AppContext):
        self.context = context
        self.domain_manager = context.domain_manager
        self.logger = logging.getLogger(__name__)

    def get_accounts(self, bank):
        """Retrieve accounts for the specified bank."""
        try:
            adapter = self.context.adapter_manager.get_bank_adapter(bank)
            accounts = adapter.get_accounts()

            success_message = f"Successfully retrieved {len(accounts)} accounts for bank {bank}"
            log_info(self.logger, success_message)

            return self._format_success(accounts, success_message, status.HTTP_200_OK)

        except Exception as e:
            error_message = f"Unexpected error retrieving accounts for bank '{bank}': {str(e)}"
            log_error(self.logger, error_message)

            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)