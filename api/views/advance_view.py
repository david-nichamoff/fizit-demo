import logging

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema

from api.serializers.advance_serializer import AdvanceSerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.interfaces import AdvanceAPI

from api.mixins.shared import ValidationMixin
from api.mixins.views import PermissionMixin

from api.utilities.logging import log_error, log_info, log_warning
from api.utilities.validation import is_valid_integer

class AdvanceViewSet(viewsets.ViewSet, ValidationMixin, PermissionMixin):
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        """Initialize the view with AdvanceAPI instance and logger."""
        super().__init__(*args, **kwargs)
        self.advance_api = AdvanceAPI()
        self.logger = logging.getLogger(__name__)

    @extend_schema(
        tags=["Advances"],
        responses={status.HTTP_200_OK: AdvanceSerializer(many=True)},
        summary="Get Advance Amounts",
        description="Get the current advance amounts for a contract as a list.",
    )
    def list(self, request, contract_idx=None):
        """
        Retrieve a list of advance amounts for a specific contract.
        """
        log_info(self.logger, f"Fetching advance amounts for contract {contract_idx}")

        try:
            # Validate contract_idx
            if not is_valid_integer(contract_idx):
                raise ValidationError("Contract_idx must be an integer")

            # Fetch advances using AdvanceAPI
            response = self.advance_api.get_advances(int(contract_idx))

            if response["status"] == status.HTTP_200_OK:
                # Serialize the data and return
                serializer = AdvanceSerializer(response["data"], many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=["Advances"],
        request=AdvanceSerializer,
        responses={status.HTTP_201_CREATED: dict},
        summary="Initiate Advance Payment",
        description="Initiate advance payment.",
    )
    def create(self, request, contract_idx=None):
        """
        Create advance payments for a specific contract.
        """
        log_info(self.logger, f"Initiating advance payment for contract {contract_idx}")
        auth_info = request.auth

        try:
            # Validate master key and contract_idx
            self._validate_master_key(auth_info)

            if not is_valid_integer(contract_idx):
                raise ValidationError("Contract_idx must be an integer")

            # Validate request data
            serializer = AdvanceSerializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            log_info(self.logger, f"Validated advance payment data for contract {contract_idx}")

            # Add advances using AdvanceAPI
            response = self.advance_api.add_advances(int(contract_idx), serializer.validated_data)

            if response["status"] == status.HTTP_201_CREATED:
                log_info(self.logger, f"Successfully initiated advance payments for contract {contract_idx}")
                return Response(response["data"], status=status.HTTP_201_CREATED)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except PermissionDenied as pd:
            log_warning(self.logger, f"Permission denied for contract {contract_idx}: {pd}")
            return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)