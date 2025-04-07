import logging

from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.managers.app_context import AppContext
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning

class RecipientAPI(ResponseMixin):

    def __init__(self, context: AppContext):
        self.context = context
        self.config_manager = context.config_manager
        self.domain_manager = context.domain_manager
        self.logger = logging.getLogger(__name__)

    def get_recipients(self, bank):
        try:
            adapter = self.context.adapter_manager.get_bank_adapter(bank)
            recipients = adapter.get_recipients()
            success_message = f"Successfully retrieved {len(recipients)} recipients for bank {bank}"
            return self._format_success(recipients, success_message, status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Validation error retrieving recipients for bank {bank} : {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error retrieving recipients for bank '{bank}': {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)
