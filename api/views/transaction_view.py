import logging

from dateutil import parser as date_parser
from datetime import timezone

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import viewsets, status

from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.transaction_serializer import TransactionSerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.interfaces import TransactionAPI, PartyAPI
from api.registry import RegistryManager
from api.views.mixins.validation import ValidationMixin
from api.views.mixins.permission import PermissionMixin
from api.utilities.logging import log_error, log_info, log_warning
from api.utilities.validation import is_valid_integer

class TransactionViewSet(viewsets.ViewSet, ValidationMixin, PermissionMixin):
    """
    A ViewSet for managing transactions associated with a contract.
    """
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.transaction_api = TransactionAPI()
        self.party_api = PartyAPI()
        self.registry_manager = RegistryManager()

    @extend_schema(
        tags=["Transactions"],
        parameters=[
            OpenApiParameter(name='transact_min_dt', description='Minimum transaction date for filtering (ISO 8601 format) (inclusive)', required=False, type=str),
            OpenApiParameter(name='transact_max_dt', description='Maximum transaction date for filtering (ISO 8601 format) (exclusive)', required=False, type=str),
        ],
        responses={status.HTTP_200_OK: TransactionSerializer(many=True)},
        summary="List Transactions",
        description="Retrieve a list of transactions associated with a contract.",
    )
    def list(self, request, contract_type=None, contract_idx=None):
        log_info(self.logger, f"Fetching transactions for {contract_type}:{contract_idx}.")

        try:
            contract_api = self.registry_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.registry_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            # Parse optional date filters
            transact_min_dt = self.parse_optional_date(request.query_params.get('transact_min_dt'))
            transact_max_dt = self.parse_optional_date(request.query_params.get('transact_max_dt'))

            # Fetch parties and transactions
            response = self.party_api.get_parties(contract_type, int(contract_idx))

            if response["status"] == status.HTTP_200_OK:
                parties = response["data"]
            else:
                return Response({"error" : response["message"]}, response["status"])

            response = self.transaction_api.get_transactions(
                contract_type, 
                int(contract_idx),
                request.auth.get("api_key"),
                parties,
                transact_min_dt=transact_min_dt,
                transact_max_dt=transact_max_dt,
            )

            if response["status"] == status.HTTP_200_OK:
                # Serialize and return the data
                serializer = TransactionSerializer(response["data"], many=True)
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
        tags=["Transactions"],
        request=TransactionSerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Create Transactions",
        description="Add a list of transactions to an existing contract.",
    )
    def create(self, request, contract_type=None, contract_idx=None):
        """
        Add transactions to a contract.
        """
        log_info(self.logger, f"Creating transactions for {contract_type}:{contract_idx}.")

        try:
            self._validate_master_key(request.auth)
            contract_api = self.registry_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.registry_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            # Validate request data
            validated_data = self._validate_request_data(TransactionSerializer, request.data, many=True)
            self._validate_transactions(validated_data)

            response = contract_api.get_contract(contract_type, contract_idx, request.auth.get("api_key"))
            transact_logic = response["data"]["transact_logic"]

            response = self.transaction_api.add_transactions(contract_type, contract_idx, transact_logic, validated_data, api_key=request.auth.get("api_key"))

            if response["status"] == status.HTTP_201_CREATED:
                # Serialize and return the data
                return Response(response["data"], status=status.HTTP_201_CREATED)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except PermissionDenied as pd:
            log_warning(self.logger, f"Permission denied for {contract_type}:{contract_idx}: {pd}")
            return Response({"detail": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=["Transactions"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Transactions",
        description="Delete all transactions from a contract.",
    )
    def destroy(self, request, contract_type=None, contract_idx=None):
        log_info(self.logger, f"Deleting transactions for {contract_type}:{contract_idx}.")

        try:
            self._validate_master_key(request.auth)
            contract_api = self.registry_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.registry_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            # Delete transactions via TransactionAPI
            response = self.transaction_api.delete_transactions(contract_type, contract_idx)

            if response["status"] == status.HTTP_204_NO_CONTENT:
                return Response(response["data"], status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except PermissionDenied as pd:
            log_warning(self.logger, f"Permission denied for {contract_type}:{contract_idx}: {pd}")
            return Response({"detail": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def parse_optional_date(self, date_str):
        """
        Parse and validate optional date parameters.
        """
        if not date_str:
            return None
        try:
            return date_parser.isoparse(date_str).astimezone(timezone.utc)
        except ValidationError:
            log_warning(self.logger, f"Invalid date format: {date_str}")
            raise ValidationError(f"Invalid date format. Expected ISO 8601 format.")