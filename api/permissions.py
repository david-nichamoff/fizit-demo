# permissions.py
from rest_framework.permissions import BasePermission

from .models.api_key_models import CustomAPIKey

class HasCustomAPIKey(BasePermission):
    def has_permission(self, request, view):
        key = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        if key.startswith('Api-Key '):
            key = key.split(' ')[-1]
        try:
            api_key = CustomAPIKey.objects.get_from_key(key)
            if api_key and api_key.is_valid:
                return True
        except CustomAPIKey.DoesNotExist:
            return False
        return False