from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .managers.secrets_manager import SecretsManager  

class AWSSecretsAPIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Get the API key from the request's Authorization header
        api_key = request.META.get('HTTP_AUTHORIZATION')
        if not api_key:
            return None  # No API key provided, return None to try the next authentication method
        
        # Remove "Api-Key " prefix, if exists
        api_key = api_key.replace("Api-Key ", "")

        # Initialize the SecretsManager and load the keys
        secrets_manager = SecretsManager()
        valid_keys = secrets_manager.load_keys()

        # Check for the special master key (FIZIT_MASTER_KEY)
        master_key = valid_keys.get("FIZIT_MASTER_KEY")

        if api_key == master_key:
            # If the API key is the master key, return special handling (like elevated privileges)
            return (None, {'is_master_key': True})  # You can pass a flag for master key

        # Check if the provided API key is valid
        if api_key not in valid_keys.values():
            raise AuthenticationFailed('Invalid API key')

        # If valid, return the user and API key (Django expects a user object, 
        # you can return None if you're not doing user-level authentication)
        return (None, {'is_master_key': False})  # Normal API key