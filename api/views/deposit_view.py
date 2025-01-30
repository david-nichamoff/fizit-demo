import logging

from datetime import datetime, timedelta

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import viewsets, status

from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.deposit_serializer import DepositSerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.interfaces import DepositAPI
from api.registry import RegistryManager
from api.views.mixins.validation import ValidationMixin
from api.views.mixins.permission import PermissionMixin
from api.utilities.logging import log_info, log_warning, log_error
from api.utilities.validation import is_valid_integer


class DepositViewSet(viewsets.ViewSet, ValidationMixin, PermissionMixin):
    """
    A ViewSet for managing deposit-related operations.
    """
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.deposit_api = DepositAPI()
        self.registry_manager = RegistryManager()
        self.logger = logging.getLogger(__name__)

    @extend_schema(
        tags=["Deposits"],
        parameters=[
            OpenApiParameter(
                name='start_date',
                description='Start date for filtering deposits in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)',
                required=True,
                type=str,
                default=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
            ),
            OpenApiParameter(
                name='end_date',
                description='End date for filtering deposits in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)',
                required=True,
                type=str,
                default=datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            ),
        ],
        responses={status.HTTP_200_OK: DepositSerializer(many=True)},
        summary="List Deposits",
        description="Retrieve a list of potential bank deposits for a contract."
    )
    def list(self, request, contract_type=None, contract_idx=None):
        """Retrieve a list of deposits for a specific contract."""
        log_info(self.logger, f"Retrieving deposits for {contract_type}:{contract_idx}")

        try:
            contract_api = self.registry_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.registry_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            # Parse and validate date range
            start_date, end_date = self.parse_date_range(request)
            response = self.deposit_api.get_deposits(start_date, end_date, contract_type, int(contract_idx))

            if response["status"] == status.HTTP_200_OK:
                return Response(response["data"], status=status.HTTP_200_OK)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=["Deposits"],
        request=DepositSerializer,
        responses={status.HTTP_201_CREATED: dict},
        summary="Add Settlement Deposit",
        description="Add a bank deposit to a settlement period."
    )
    def create(self, request, contract_type=None, contract_idx=None):
        """Add deposit to a settlement for a specific contract."""
        log_info(self.logger, f"Attempting to add deposit for {contract_type}:{contract_idx}")

        try:
            # Validate master key and contract_idx
            self._validate_master_key(request.auth)
            contract_api = self.registry_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.registry_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            # Validate request data
            validated_data = self._validate_request_data(DepositSerializer, request.data, many=False)
            response = self.deposit_api.add_deposit(contract_type, int(contract_idx), validated_data)

            log_info(self.logger, f"Posted deposit with {response}")

            if response["status"] == status.HTTP_201_CREATED:
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

    def parse_date_range(self, request):
        """
        Parse and validate start_date and end_date from query parameters.
        """
        try:
            start_date = datetime.fromisoformat(request.query_params.get('start_date'))
            end_date = datetime.fromisoformat(request.query_params.get('end_date'))

            # Validate date range
            if start_date >= end_date:
                raise ValidationError("start_date must be earlier than end_date.")

            return start_date, end_date

        except Exception as e:
            log_error(self.logger, f"Invalid date range provided: {e}")
            raise ValidationError("Invalid date range format. Ensure dates are in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).")