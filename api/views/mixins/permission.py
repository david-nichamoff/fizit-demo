from rest_framework.exceptions import PermissionDenied

class PermissionMixin:
    """Reusable mixin for validating permissions."""
    def _validate_master_key(self, auth_info):
        """Ensure the master key is present and valid."""
        if not auth_info.get('is_master_key', False):
            raise PermissionDenied("You do not have permission to perform this action.")
