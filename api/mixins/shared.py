from rest_framework.exceptions import ValidationError
from rest_framework import status


class ValidationMixin:

    def _validate_contract_idx(self, contract_idx, contract_api):
        if contract_idx is None:
            raise ValidationError("contract_idx is required.")
        
        # Fetch contract count
        contract_count_response = contract_api.get_contract_count()
        if contract_count_response["status"] != status.HTTP_200_OK:
            raise ValidationError("Unable to retrieve contract count.")

        contract_count = contract_count_response["data"]["count"]
        if contract_idx < 0 or contract_idx >= contract_count:
            raise ValidationError(f"Invalid contract_idx: {contract_idx}. Must be between 0 and {contract_count - 1}.")

    def _validate_query_param(self, param_name, param_value, expected_values=None):
        """Validate query parameters."""
        if not param_value:
            raise ValidationError(f"Query parameter '{param_name}' is required.")
        if expected_values and param_value not in expected_values:
            raise ValidationError(f"Invalid value for query parameter '{param_name}'. Expected one of {expected_values}.")

    def _validate_request_data(self, serializer_class, data, many=False, partial=False):
        """Validate request data using a serializer."""
        serializer = serializer_class(data=data, partial=partial, many=many)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def _validate_optional_integer(self, param_name, param_value):
        """Validate an optional integer query parameter."""
        if param_value is not None:
            try:
                int(param_value)

            except Exception as e:
                raise ValidationError(f"Query parameter '{param_name}' must be an integer.")

    def _validate_optional_string(self, param_name, param_value):
        """Validate an optional string query parameter."""
        if param_value is not None and not isinstance(param_value, str):
            raise ValidationError(f"Query parameter '{param_name}' must be a string.")