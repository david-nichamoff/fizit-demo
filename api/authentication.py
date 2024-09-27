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
            raise AuthenticationFailed('Authorization header missing or empty')

        # Ensure API key has the correct prefix and remove it
        if not api_key.startswith("Api-Key "):
            logger.warning("Authorization header does not start with 'Api-Key '. Header: %s", api_key)
            raise AuthenticationFailed('Authorization header must start with "Api-Key "')

        api_key = api_key.replace("Api-Key ", "", 1)
        logger.info("Extracted API key.")

        try:
            # Initialize the SecretsManager and load the keys
            secrets_manager = SecretsManager()
            valid_keys = secrets_manager.load_keys()  # Expecting valid_keys to be a dictionary
            logger.info("Loaded valid keys from SecretsManager.")
        except Exception as e:
            logger.error("Error loading keys from SecretsManager: %s", str(e))
            raise AuthenticationFailed('Error loading API keys.')

        # Check for the FIZIT_MASTER_KEY in the loaded keys
        master_key = valid_keys.get("FIZIT_MASTER_KEY")
        if master_key:
            logger.info("Master key loaded for comparison.")
            if api_key == master_key:
                logger.info("Master key used for authentication.")
                return (None, {'api_key': api_key, 'is_master_key': True})

        # Check if the provided API key matches any of the loaded keys
        if api_key in valid_keys.values():
            logger.info("Successfully authenticated using API key.")
            return (None, {'api_key': api_key, 'is_master_key': False})

        # Log and raise an error if the API key doesn't match
        logger.warning("Invalid API key provided: %s", api_key)
        raise AuthenticationFailed('Invalid API key')

    def authenticate_header(self, request):
        """
        This method returns the value for the 'WWW-Authenticate' header, 
        which is used when an authentication failure occurs and a 401 response is returned.
        """
        logger.info("Returning authentication header: 'Api-Key'")
        return 'Api-Key'  # The client will know to use 'Api-Key {your_key}' in the Authorization header