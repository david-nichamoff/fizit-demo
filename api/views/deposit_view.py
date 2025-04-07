import logging
from datetime import datetime, timedelta

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import viewsets, status

from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.serializers.deposit_serializer import DepositSerializer
from api.views.mixins import ValidationMixin, PermissionMixin
from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_info, log_warning, log_error

class DepositViewSet(viewsets.ViewSet, ValidationMixin, PermissionMixin):
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = build_app_context()
        self.logger = logging.getLogger(__name__)

### **Purchase Contract Deposits**

    @extend_schema(
        tags=["Purchase Contracts"],
        parameters=[
            OpenApiParameter(
                name='start_date',
                description='Start date for filtering deposits (ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ)',
                required=True,
                type=str,
                default=(datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
            ),
            OpenApiParameter(
                name='end_date',
                description='End date for filtering deposits (ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ)',
                required=True,
                type=str,
                default=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            ),
        ],
        responses={status.HTTP_200_OK: DepositSerializer(many=True)},
        summary="List Purchase Contract Deposits",
        description="Retrieve a list of deposits associated with a purchase contract."
    )
    def list_purchase_deposits(self, request, contract_idx=None):
        return self._list_deposits(request, "purchase", contract_idx)

    @extend_schema(
        tags=["Purchase Contracts"],
        request=DepositSerializer,
        responses={status.HTTP_201_CREATED: dict},
        summary="Add Purchase Contract Deposit",
        description="Add a deposit to a purchase contract."
    )
    def create_purchase_deposits(self, request, contract_idx=None):
        return self._create_deposit(request, "purchase", contract_idx)


### **Sale Contract Deposits**

    @extend_schema(
        tags=["Sale Contracts"],
        parameters=[
            OpenApiParameter(
                name='start_date',
                description='Start date for filtering deposits (ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ)',
                required=True,
                type=str,
                default=(datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
            ),
            OpenApiParameter(
                name='end_date',
                description='End date for filtering deposits (ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ)',
                required=True,
                type=str,
                default=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            ),
        ],
        responses={status.HTTP_200_OK: DepositSerializer(many=True)},
        summary="List Sale Contract Deposits",
        description="Retrieve a list of deposits associated with a sale contract."
    )
    def list_sale_deposits(self, request, contract_idx=None):
        return self._list_deposits(request, "sale", contract_idx)

    @extend_schema(
        tags=["Sale Contracts"],
        request=DepositSerializer,
        responses={status.HTTP_201_CREATED: dict},
        summary="Add Sale Contract Deposit",
        description="Add a deposit to a sale contract."
    )
    def create_sale_deposits(self, request, contract_idx=None):
        return self._create_deposit(request, "sale", contract_idx)


### **Advance Contract Deposits**

    @extend_schema(
        tags=["Advance Contracts"],
        parameters=[
            OpenApiParameter(
                name='start_date',
                description='Start date for filtering deposits (ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ)',
                required=True,
                type=str,
                default=(datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
            ),
            OpenApiParameter(
                name='end_date',
                description='End date for filtering deposits (ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ)',
                required=True,
                type=str,
                default=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            ),
        ],
        responses={status.HTTP_200_OK: DepositSerializer(many=True)},
        summary="List Advance Contract Deposits",
        description="Retrieve a list of deposits associated with an advance contract."
    )
    def list_advance_deposits(self, request, contract_idx=None):
        return self._list_deposits(request, "advance", contract_idx)

    @extend_schema(
        tags=["Advance Contracts"],
        request=DepositSerializer,
        responses={status.HTTP_201_CREATED: dict},
        summary="Add Advance Contract Deposit",
        description="Add a deposit to an advance contract."
    )
    def create_advance_deposits(self, request, contract_idx=None):
        return self._create_deposit(request, "advance", contract_idx)


### **Core Functions**

    def _list_deposits(self, request, contract_type, contract_idx):
        log_info(self.logger, f"Retrieving deposits for {contract_type}:{contract_idx}")

        try:
            self._validate_contract_type(contract_type, self.context.domain_manager)
            contract_api = self.context.api_manager.get_contract_api(contract_type)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            party_api = self.context.api_manager.get_party_api()
            party_response = party_api.get_parties(contract_type, contract_idx)
            if party_response["status"] != status.HTTP_200_OK:
                return Response({"error": party_response["message"]}, party_response["status"])
            parties = party_response["data"]

            start_date, end_date = self._parse_date_range(request)
            deposit_api = self.context.api_manager.get_deposit_api(contract_type)
            response = deposit_api.get_deposits(start_date, end_date, contract_type, int(contract_idx), parties)

            if response["status"] == status.HTTP_200_OK:
                serializer = DepositSerializer(response["data"], many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": response["message"]}, status=response["status"])

        except ValidationError as e:
            log_error(self.logger, f"Validation error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_deposit(self, request, contract_type, contract_idx):
        log_info(self.logger, f"Attempting to add deposit for {contract_type}:{contract_idx}")

        try:
            self._validate_master_key(request.auth)
            self._validate_contract_type(contract_type, self.context.domain_manager)
            contract_api = self.context.api_manager.get_contract_api(contract_type)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            validated_data = self._validate_request_data(DepositSerializer, request.data)
            deposit_api = self.context.api_manager.get_deposit_api(contract_type)
            response = deposit_api.add_deposit(contract_type, int(contract_idx), validated_data)

            if response["status"] == status.HTTP_201_CREATED:
                return Response(response["data"], status=status.HTTP_201_CREATED)
            else:
                return Response({"error": response["message"]}, status=response["status"])

        except PermissionDenied as pd:
            log_error(self.logger, f"Permission denied for contract {contract_idx}: {pd}")
            return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _parse_date_range(self, request):
        """
        Parse and validate start_date and end_date from query parameters.
        """
        try:
            start_date = datetime.fromisoformat(request.query_params.get('start_date'))
            end_date = datetime.fromisoformat(request.query_params.get('end_date'))

            if start_date >= end_date:
                raise ValidationError("start_date must be earlier than end_date.")

            return start_date, end_date

        except Exception as e:
            log_error(self.logger, f"Invalid date range provided: {e}")
            raise ValidationError("Invalid date range format. Ensure dates are in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).")