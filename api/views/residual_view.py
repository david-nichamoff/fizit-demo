import logging
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import viewsets, status

from drf_spectacular.utils import extend_schema

from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.serializers import ResidualSerializer
from api.views.mixins import ValidationMixin, PermissionMixin
from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_error, log_info, log_warning

class ResidualViewSet(viewsets.ViewSet, ValidationMixin, PermissionMixin):
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = build_app_context()
        self.logger = logging.getLogger(__name__)

### **Advance Contract Residuals**

    @extend_schema(
        tags=["Advance Contracts"],
        responses={status.HTTP_200_OK: ResidualSerializer(many=True)},
        summary="List Advance Contract Residuals",
        description="Retrieve a list of residuals associated with an advance contract."
    )
    def list_advance_residuals(self, request, contract_idx=None):
        return self._list_residuals(request, "advance", contract_idx)

    @extend_schema(
        tags=["Advance Contracts"],
        request=ResidualSerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Create Advance Contract Residuals",
        description="Initiate residual payments for an advance contract."
    )
    def create_advance_residuals(self, request, contract_idx=None):
        return self._create_residuals(request, "advance", contract_idx)

### **Core Functions**

    def _list_residuals(self, request, contract_type, contract_idx):
        log_info(self.logger, f"Fetching residuals for {contract_type}:{contract_idx}.")

        try:
            self._validate_contract_type(contract_type, self.context.domain_manager)

            # Fetch contract, transactions, parties
            contract_api = self.context.api_manager.get_contract_api(contract_type)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)
            contract_response = contract_api.get_contract(contract_type, contract_idx)
            if contract_response["status"] != status.HTTP_200_OK:
                return Response({"error": contract_response["message"]}, contract_response["status"])
            contract = contract_response["data"]

            party_api = self.context.api_manager.get_party_api()
            party_response = party_api.get_parties(contract_type, contract_idx)
            if party_response["status"] != status.HTTP_200_OK:
                return Response({"error": party_response["message"]}, party_response["status"])
            parties = party_response["data"]

            settlement_api = self.context.api_manager.get_settlement_api(contract_type)
            settlement_response = settlement_api.get_settlements(contract_type, contract_idx)
            if settlement_response["status"] != status.HTTP_200_OK:
                return Response({"error": settlement_response["message"]}, settlement_response["status"])
            settlements = settlement_response["data"]

            residual_api = self.context.api_manager.get_residual_api(contract_type)
            response = residual_api.get_residuals(contract, parties, settlements)

            if response["status"] == status.HTTP_200_OK:
                serializer = ResidualSerializer(response["data"], many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": response["message"]}, status=response["status"])

        except ValidationError as e:
            log_error(self.logger, f"Validation error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_residuals(self, request, contract_type, contract_idx):
        log_info(self.logger, f"Initiating residual payment for {contract_type}:{contract_idx}")

        try:
            self._validate_master_key(request.auth)
            contract_api = self.context.api_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.context.domain_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            serializer = ResidualSerializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)

            residual_api = self.context.api_manager.get_residual_api(contract_type)
            response = residual_api.add_residuals(contract_type, int(contract_idx), serializer.validated_data)

            if response["status"] == status.HTTP_201_CREATED:
               log_info(self.logger, f"Successfully initiated residual payments for {contract_type}:{contract_idx}")
               return Response(response["data"], status=status.HTTP_201_CREATED)
            else:
                return Response({"error": response["message"]}, status=response["status"])

        except PermissionDenied as pd:
            log_error(self.logger, f"Permission denied for {contract_type}:{contract_idx}: {pd}")
            return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)