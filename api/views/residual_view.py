import logging

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import viewsets, status

from drf_spectacular.utils import extend_schema

from api.serializers.residual_serializer import ResidualSerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.interfaces import ResidualAPI
from api.registry import RegistryManager
from api.views.mixins.validation import ValidationMixin
from api.views.mixins.permission import PermissionMixin
from api.utilities.logging import log_error, log_info, log_warning
from api.utilities.validation import is_valid_integer

class ResidualViewSet(viewsets.ViewSet, ValidationMixin, PermissionMixin):
    """
    A ViewSet for managing residuals.
    """
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.residual_api = ResidualAPI()
        self.registry_manager = RegistryManager()
        self.logger = logging.getLogger(__name__)

    @extend_schema(
        tags=["Residuals"],
        responses={status.HTTP_200_OK: ResidualSerializer(many=True)},
        summary="Get Residual Amounts",
        description="Retrieve the current residual amounts for a contract as a list.",
    )
    def list(self, request, contract_type=None, contract_idx=None):
        """
        Retrieve a list of residual amounts for a given contract.
        """
        log_info(self.logger, f"Fetching residuals for {contract_type}:{contract_idx}.")

        try:
            contract_api = self.registry_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.registry_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            # Fetch residuals from ResidualAPI
            response = self.residual_api.get_residuals(contract_type, int(contract_idx))

            if response["status"] == status.HTTP_200_OK:
                # Serialize and return the data
                serializer = ResidualSerializer(response["data"], many=True)
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
        tags=["Residuals"],
        request=ResidualSerializer,
        responses={status.HTTP_201_CREATED: dict},
        summary="Initiate Residual Payment",
        description="Initiate residual payment for a contract.",
    )
    def create(self, request, contract_type=None, contract_idx=None):
        """
        Initiate a residual payment for a contract.
        """
        log_info(self.logger, f"Initiating residual payment for {contract_type}:{contract_idx}.")
        try:
            # Validate master key and contract_idx
            self._validate_master_key(request.auth)
            contract_api = self.registry_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.registry_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            # Validate request data
            validated_data = self._validate_request_data(ResidualSerializer, request.data, many=True)

            # Add residuals via ResidualAPI
            response = self.residual_api.add_residuals(contract_type, int(contract_idx), validated_data)

            if response["status"] == status.HTTP_201_CREATED:
                # Serialize and return the data
                return Response(response["data"], status=status.HTTP_201_CREATED)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except PermissionDenied as pd:
            log_warning(self.logger, f"Permission denied for {contract_type}:{contract_idx}: {pd}")
            return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)