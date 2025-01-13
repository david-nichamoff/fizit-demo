from rest_framework.exceptions import ValidationError
from api.utilities.logging import  log_error, log_info, log_warning

class AdapterMixin:
    def _get_bank_adapter(self, bank):
        """Retrieve the appropriate adapter based on the bank type."""

        if bank == "mercury":
            return self.mercury_adapter
        elif bank == "token":
            return self.token_adapter

        error_message = f"Unsupported bank type: '{bank}'"
        raise ValidationError(error_message)


class InterfaceResponseMixin:
    def _format_success(self, data, success_message, success_status):

        if hasattr(self, "logger"):
            log_info(self.logger, success_message)

        return { 
            "status": success_status, 
            "data": data 
        }

    def _format_error(self, error_message, error_status):
        if hasattr(self, "logger"):
            log_error(self.logger, error_message)
        
        return {
            "status": error_status,
            "message": error_message,
        }