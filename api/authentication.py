import logging
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .managers.secrets_manager import SecretsManager  

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
        logger.info("Starting authentication process.")

        if not api_key:
            logger.warning("Authorization header missing or empty.")
            raise AuthenticationFailed('Authorization header missing or empty')  # Explicit error for missing API key
        
        # Ensure API key has the correct prefix and remove it
        if not api_key.startswith("Api-Key "):
            logger.warning("Authorization header does not start with 'Api-Key '. Header: %s", api_key)
            raise AuthenticationFailed('Authorization header must start with "Api-Key "')
        
        api_key = api_key.replace("Api-Key ", "", 1)  # Only replace once, to avoid unexpected issues
        logger.info("Extracted API key: %s", api_key)

        try:
            # Initialize the SecretsManager and load the keys
            secrets_manager = SecretsManager()
            valid_keys = secrets_manager.load_keys()
            logger.info("Loaded valid keys from SecretsManager.")

        except Exception as e:
            logger.error("Error loading keys from SecretsManager: %s", str(e))
            raise AuthenticationFailed('Error loading API keys.')

        # Check for the special master key (FIZIT_MASTER_KEY)
        master_key = valid_keys.get("FIZIT_MASTER_KEY")
        logger.info("Master key loaded for comparison.")

        if api_key == master_key:
            logger.info("Master key used for authentication.")
            return (None, {'is_master_key': True})  # You can pass a flag for master key

        # Check if the provided API key is valid
        if api_key not in valid_keys.values():
            logger.warning("Invalid API key provided: %s", api_key)
            raise AuthenticationFailed('Invalid API key')  # Raise explicit invalid API key error

        # If valid, return None as user and pass is_master_key flag as False
        logger.info("Successfully authenticated using API key.")
        return (None, {'is_master_key': False})  # Normal API key handling

    def authenticate_header(self, request):
        """
        This method returns the value for the 'WWW-Authenticate' header, 
        which is used when an authentication failure occurs and a 401 response is returned.
        """
        logger.info("Returning authentication header: 'Api-Key'")
        return 'Api-Key'  # The client will know to use 'Api-Key {your_key}' in the Authorization header