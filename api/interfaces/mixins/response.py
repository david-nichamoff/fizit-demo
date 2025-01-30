from api.utilities.logging import  log_error, log_info, log_warning

class ResponseMixin:
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