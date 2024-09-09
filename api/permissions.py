from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed
from api.authentication import AWSSecretsAPIKeyAuthentication

class HasCustomAPIKey(BasePermission):
    def has_permission(self, request, view):
        # Initialize AWSSecretsAPIKeyAuthentication to authenticate the request
        auth = AWSSecretsAPIKeyAuthentication()

        try:
            user, auth_info = auth.authenticate(request)  # This returns the user and whether it's the master key
            if auth_info.get('is_master_key', False):
                # If the API key is the master key, allow access
                return True
        except AuthenticationFailed:
            # If authentication fails, deny permission
            return False

        # If authentication was successful and it's not the master key, grant access
        if auth_info and not auth_info.get('is_master_key'):
            return True

        return False