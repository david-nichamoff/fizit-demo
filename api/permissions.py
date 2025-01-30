from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied, ValidationError
from api.authentication import AWSSecretsAPIKeyAuthentication

class HasCustomAPIKey(BasePermission):
    def has_permission(self, request, view):
        # Initialize AWSSecretsAPIKeyAuthentication to authenticate the request
        auth = AWSSecretsAPIKeyAuthentication()

        try:
            result = auth.authenticate(request)  # Try to authenticate the request
            if result is None:  # If authentication fails, let it raise a 401
                raise AuthenticationFailed('Request not authorized: API key missing or invalid')

            user, auth_info = result

            # If the API key is the master key, allow access
            if auth_info.get('is_master_key', False):
                return True

        except AuthenticationFailed as e:
            # If authentication fails, raise a 401 Unauthorized error
            raise AuthenticationFailed(str(e))

        # If the authentication was successful but it's not the master key, grant access
        if auth_info and not auth_info.get('is_master_key'):
            return True

        # If the user is authenticated but lacks permission, raise a 403 Forbidden error
        raise PermissionDenied('You do not have permission to perform this action')