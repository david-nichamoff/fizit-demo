import logging

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import viewsets, status

from drf_spectacular.utils import extend_schema

from api.serializers.advance_serializer import AdvanceSerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.views.mixins import ValidationMixin, PermissionMixin
from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_error, log_info, log_warning

class AdvanceViewSet(viewsets.ViewSet, ValidationMixin, PermissionMixin):
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        """Initialize the view with AdvanceAPI instance and logger."""
        super().__init__(*args, **kwargs)
        self.context = build_app_context()
        self.logger = logging.getLogger(__name__)

### **Purchase Advances**

    @extend_schema(
        tags=["Purchase Contracts"],
        responses={status.HTTP_200_OK: AdvanceSerializer(many=True)},
        summary="List Purchase Advances",
        description="Retrieve a list of advances associated with a purchase contract.",
    )
    def list_purchase_advances(self, request, contract_idx=None):
        return self._list_advances(request, "purchase", contract_idx)

    @extend_schema(
        tags=["Purchase Contracts"],
        request=AdvanceSerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Create Purchase Advances",
        description="Initiate advance payments for a purchase contract.",
    )
    def create_purchase_advances(self, request, contract_idx=None):
        return self._create_advances(request, "purchase", contract_idx)

### **Sale Advances**

    @extend_schema(
        tags=["Sale Contracts"],
        responses={status.HTTP_200_OK: AdvanceSerializer(many=True)},
        summary="List Sale Advances",
        description="Retrieve a list of advances associated with a sale contract.",
    )
    def list_sale_advances(self, request, contract_idx=None):
        return self._list_advances(request, "sale", contract_idx)

    @extend_schema(
        tags=["Sale Contracts"],
        request=AdvanceSerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Create Sale Advances",
        description="Initiate advance payments for a sale contract.",
    )
    def create_sale_advances(self, request, contract_idx=None):
        return self._create_advances(request, "sale", contract_idx)

### **Advance Contracts**

    @extend_schema(
        tags=["Advance Contracts"],
        responses={status.HTTP_200_OK: AdvanceSerializer(many=True)},
        summary="List Advance Contract Advances",
        description="Retrieve a list of advances associated with an advance contract.",
    )
    def list_advance_advances(self, request, contract_idx=None):
        return self._list_advances(request, "advance", contract_idx)

    @extend_schema(
        tags=["Advance Contracts"],
        request=AdvanceSerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Create Advance Contract Advances",
        description="Initiate advance payments for an advance contract.",
    )
    def create_advance_advances(self, request, contract_idx=None):
        return self._create_advances(request, "advance", contract_idx)

### **Core Functions**

    def _list_advances(self, request, contract_type, contract_idx):
        log_info(self.logger, f"Fetching advances for {contract_type}:{contract_idx}")

        try:
            self._validate_contract_type(contract_type, self.context.domain_manager)

            # Fetch contract, transactions, parties
            contract_api = self.context.api_manager.get_contract_api(contract_type)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)
            contract_response = contract_api.get_contract(contract_type, contract_idx)
            if contract_response["status"] != status.HTTP_200_OK:
                return Response({"error": contract_response["message"]}, contract_response["status"])
            contract = contract_response["data"]

            transaction_api = self.context.api_manager.get_transaction_api(contract_type)
            transaction_response = transaction_api.get_transactions(contract_type, contract_idx)
            if transaction_response["status"] != status.HTTP_200_OK:
                return Response({"error": transaction_response["message"]}, transaction_response["status"])
            transactions = transaction_response["data"]

            party_api = self.context.api_manager.get_party_api()
            party_response = party_api.get_parties(contract_type, contract_idx)
            if party_response["status"] != status.HTTP_200_OK:
                return Response({"error": party_response["message"]}, party_response["status"])
            parties = party_response["data"]

            funding_bank = contract.get("funding_instr", {}).get("bank")
            if not funding_bank:
                log_error(self.logger, f"Funding bank not found in contract {contract_type}:{contract_idx}")
                return Response({"error": "Funding bank not found"}, status=status.HTTP_400_BAD_REQUEST)

            account_api = self.context.api_manager.get_account_api()
            accounts_response = account_api.get_accounts(funding_bank)
            if accounts_response["status"] != status.HTTP_200_OK:
                return Response({"error": accounts_response["message"]}, accounts_response["status"])
            accounts = accounts_response["data"]

            recipient_api = self.context.api_manager.get_recipient_api()
            recipients_response = recipient_api.get_recipients(funding_bank)
            if recipients_response["status"] != status.HTTP_200_OK:
                return Response({"error": recipients_response["message"]}, recipients_response["status"])
            recipients = recipients_response["data"]

            advance_api = self.context.api_manager.get_advance_api(contract_type)
            response = advance_api.get_advances(contract, transactions, parties, accounts, recipients)

            if response["status"] == status.HTTP_200_OK:
                serializer = AdvanceSerializer(response["data"], many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": response["message"]}, response["status"])

        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_advances(self, request, contract_type, contract_idx):
        log_info(self.logger, f"Initiating advance payment for {contract_type}:{contract_idx}")

        try:
            self._validate_master_key(request.auth)

            contract_api = self.context.api_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.context.domain_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            serializer = AdvanceSerializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)

            log_info(self.logger, f"Validated advance payment data for {contract_type}:{contract_idx}")
            advance_api = self.context.api_manager.get_advance_api(contract_type)
            response = advance_api.add_advances(contract_type, int(contract_idx), serializer.validated_data)

            if response["status"] == status.HTTP_201_CREATED:
                log_info(self.logger, f"Successfully initiated advance payments for {contract_type}:{contract_idx}")
                return Response(response["data"], status=status.HTTP_201_CREATED)
            else:
                return Response({"error": response["message"]}, response["status"])

        except PermissionDenied as pd:
            log_error(self.logger, f"Permission denied for contract {contract_type}:{contract_idx}: {pd}")
            return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)