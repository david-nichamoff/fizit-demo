# authentication.py
from rest_framework.authentication import BaseAuthentication

from .models.api_key_models import CustomAPIKey

class CustomAPIKeyAuthentication(BaseAuthentication):
    model = CustomAPIKey

    class APIKeyUser:
        is_authenticated = True

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Api-Key '):
            key = auth_header.split(' ')[-1]
            try:
                api_key = self.model.objects.get_from_key(key)
                if api_key and api_key.is_valid:
                    return (self.APIKeyUser(), None)
            except CustomAPIKey.DoesNotExist:
                pass
        return None