import logging
from dateutil import parser as date_parser
from datetime import timezone

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import viewsets, status

from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.serializers import AdvanceTransactionSerializer, SaleTransactionSerializer, PurchaseTransactionSerializer
from api.views.mixins import ValidationMixin, PermissionMixin
from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_error, log_info, log_warning


class TransactionViewSet(viewsets.ViewSet, ValidationMixin, PermissionMixin):
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = build_app_context()
        self.logger = logging.getLogger(__name__)

### **Purchase Transactions**

    @extend_schema(
        tags=["Purchase Contracts"],
        parameters=[
            OpenApiParameter(name='transact_min_dt', description='Minimum transaction date (ISO 8601)', required=False, type=str),
            OpenApiParameter(name='transact_max_dt', description='Maximum transaction date (ISO 8601)', required=False, type=str),
        ],
        responses={status.HTTP_200_OK: PurchaseTransactionSerializer(many=True)},
        summary="List Purchase Contract Transactions",
        description="Retrieve a list of transactions associated with a purchase contract.",
    )
    def list_purchase_transactions(self, request, contract_idx=None):
        return self._list_transactions(request, "purchase", contract_idx)

    @extend_schema(
        tags=["Purchase Contracts"],
        request=PurchaseTransactionSerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Create Purchase Contract Transactions",
        description="Add transactions to a purchase contract.",
    )
    def create_purchase_transactions(self, request, contract_idx=None):
        return self._create_transactions(request, "purchase", contract_idx)

    @extend_schema(
        tags=["Purchase Contracts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Purchase Contract Transactions",
        description="Delete all transactions from a purchase contract",
    )
    def destroy_purchase_transactions(self, request, contract_idx=None):
        return self._destroy_transactions(request, "purchase", contract_idx)

### **Sale Transactions**

    @extend_schema(
        tags=["Sale Contracts"],
        parameters=[
            OpenApiParameter(name='transact_min_dt', description='Minimum transaction date (ISO 8601)', required=False, type=str),
            OpenApiParameter(name='transact_max_dt', description='Maximum transaction date (ISO 8601)', required=False, type=str),
        ],
        responses={status.HTTP_200_OK: SaleTransactionSerializer(many=True)},
        summary="List Sale Contract Transactions",
        description="Retrieve a list of transactions associated with a sale contract.",
    )
    def list_sale_transactions(self, request, contract_idx=None):
        return self._list_transactions(request, "sale", contract_idx)

    @extend_schema(
        tags=["Sale Contracts"],
        request=SaleTransactionSerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Create Sale Contract Transactions",
        description="Add transactions to a sale contract.",
    )
    def create_sale_transactions(self, request, contract_idx=None):
        return self._create_transactions(request, "sale", contract_idx)

    @extend_schema(
        tags=["Sale Contracts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Sale Contract Transactions",
        description="Delete all transactions from a sale contract.",
    )
    def destroy_sale_transactions(self, request, contract_idx=None):
        return self._destroy_transactions(request, "sale", contract_idx)

### **Advance Transactions**

    @extend_schema(
        tags=["Advance Contracts"],
        parameters=[
            OpenApiParameter(name='transact_min_dt', description='Minimum transaction date (ISO 8601)', required=False, type=str),
            OpenApiParameter(name='transact_max_dt', description='Maximum transaction date (ISO 8601)', required=False, type=str),
        ],
        responses={status.HTTP_200_OK: AdvanceTransactionSerializer(many=True)},
        summary="List Advance Contract Transactions",
        description="Retrieve a list of transactions associated with an advance contract.",
    )
    def list_advance_transactions(self, request, contract_idx=None):
        return self._list_transactions(request, "advance", contract_idx)

    @extend_schema(
        tags=["Advance Contracts"],
        request=AdvanceTransactionSerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Create Advance Contract Transactions",
        description="Add transactions to an advance contract.",
    )
    def create_advance_transactions(self, request, contract_idx=None):
        return self._create_transactions(request, "advance", contract_idx)

    @extend_schema(
        tags=["Advance Contracts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Advance Contract Transactions",
        description="Delete all transactions from an advance contract.",
    )
    def destroy_advance_transactions(self, request, contract_idx=None):
        return self._destroy_transactions(request, "advance", contract_idx)

### **Core Functions**

    def _list_transactions(self, request, contract_type, contract_idx):
        log_info(self.logger, f"Fetching transactions for {contract_type}:{contract_idx}.")

        try:
            contract_api = self.context.api_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.context.domain_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            transact_min_dt = self._parse_optional_date(request.query_params.get('transact_min_dt'))
            transact_max_dt = self._parse_optional_date(request.query_params.get('transact_max_dt'))

            party_api = self.context.api_manager.get_party_api()
            response = party_api.get_parties(contract_type, int(contract_idx))
            if response["status"] != status.HTTP_200_OK:
                return Response({"error": response["message"]}, response["status"])
            parties = response["data"]

            transaction_api = self.context.api_manager.get_transaction_api(contract_type)
            response = transaction_api.get_transactions(
                contract_type, int(contract_idx), request.auth.get("api_key"), parties,
                transact_min_dt=transact_min_dt, transact_max_dt=transact_max_dt
            )

            if response["status"] == status.HTTP_200_OK:
                serializer_class = self.context.serializer_manager.get_transaction_serializer(contract_type)
                serializer = serializer_class(response["data"], many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": response["message"]}, response["status"])

        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_transactions(self, request, contract_type, contract_idx):
        log_info(self.logger, f"Creating transactions for {contract_type}:{contract_idx}.")

        try:
            self._validate_master_key(request.auth)
            contract_api = self.context.api_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.context.domain_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            serializer_class = self.context.serializer_manager.get_transaction_serializer(contract_type)
            validated_data = self._validate_request_data(serializer_class, request.data, many=True)
            self._validate_transactions(validated_data)

            contract = contract_api.get_contract(contract_type, contract_idx, request.auth.get("api_key"))
            transact_logic = contract["data"]["transact_logic"]
            transaction_api = self.context.api_manager.get_transaction_api(contract_type)

            log_info(self.logger, f"Calling integration with the following parameters: ")
            log_info(self.logger, f"Contract_type: {contract_type}, Contract_idx: {contract_idx}")
            log_info(self.logger, f"Transact_logic: {transact_logic}, validated_data: {validated_data}")
            response = transaction_api.add_transactions(
                contract_type, contract_idx, transact_logic, validated_data
            )

            if response["status"] == status.HTTP_201_CREATED:
                return Response(response["data"], status=status.HTTP_201_CREATED)
            else:
                return Response({"error": response["message"]}, response["status"])

        except PermissionDenied as pd:
            log_error(self.logger, f"Permission denied: {pd}")
            return Response({"detail": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _destroy_transactions(self, request, contract_type, contract_idx):
        log_info(self.logger, f"Deleting transactions for {contract_type}:{contract_idx}.")

        try:
            self._validate_master_key(request.auth)
            contract_api = self.context.api_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.context.domain_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            transaction_api = self.context.api_manager.get_transaction_api(contract_type)
            response = transaction_api.delete_transactions(contract_type, contract_idx)

            if response["status"] == status.HTTP_204_NO_CONTENT:
                return Response(response["data"], status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": response["message"]}, response["status"])

        except PermissionDenied as pd:
            log_error(self.logger, f"Permission denied: {pd}")
            return Response({"detail": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _parse_optional_date(self, date_str):
        if not date_str:
            return None
        try:
            return date_parser.isoparse(date_str).astimezone(timezone.utc)
        except (ValueError, TypeError):
            log_error(self.logger, f"Invalid date format: {date_str}")
            raise ValidationError("Invalid date format. Expected ISO 8601 format.")