import logging

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed, ValidationError

from api.secrets.secrets_manager import SecretsManager  

from api.utilities.logging import  log_error, log_info, log_warning

# Configure logger
logger = logging.getLogger(__name__)

class NoAuthForSwagger(BaseAuthentication):
    def authenticate(self, request):
        # This returns None, meaning no authentication is required
        return None

class AWSSecretsAPIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Get the API key from the request's Authorization header
        api_key = request.META.get('HTTP_AUTHORIZATION')

        if not api_key:
            log_warning(logger, "Authorization header missing or empty.")
            raise AuthenticationFailed('Authorization header missing or empty')

        # Ensure API key has the correct prefix and remove it
        if not api_key.startswith("Api-Key "):
            log_warning(logger, "Authorization header does not start with 'Api-Key '. Header: %s")
            raise AuthenticationFailed('Authorization header must start with "Api-Key "')

        api_key = api_key.replace("Api-Key ", "", 1)

        secrets_manager = SecretsManager()
        valid_keys = secrets_manager.get_all_partner_keys()  # Expecting valid_keys to be a dictionary
        master_key = secrets_manager.get_master_key()

        if master_key:
            if api_key == master_key:
                return (None, {'api_key': api_key, 'is_master_key': True})

        # Check if the provided API key matches any of the loaded keys
        if api_key in valid_keys.values():
            log_info(logger, "Successfully authenticated using API key.")
            return (None, {'api_key': api_key, 'is_master_key': False})

        # Log and raise an error if the API key doesn't match
        log_warning(logger, "Invalid API key provided: %s")
        raise AuthenticationFailed('Invalid API key')

    def authenticate_header(self, request):
        """
        This method returns the value for the 'WWW-Authenticate' header, 
        which is used when an authentication failure occurs and a 401 response is returned.
        """
        return 'Api-Key'  # The client will know to use 'Api-Key {your_key}' in the Authorization header