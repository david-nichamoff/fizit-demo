import logging

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import viewsets, status

from drf_spectacular.utils import extend_schema

from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.interfaces import PartyAPI
from api.serializers import AdvanceSettlementSerializer, SaleSettlementSerializer
from api.registry import RegistryManager
from api.views.mixins.validation import ValidationMixin
from api.views.mixins.permission import PermissionMixin
from api.utilities.logging import log_error, log_info, log_warning

class SettlementViewSet(viewsets.ViewSet, ValidationMixin, PermissionMixin):
    """
    A ViewSet for managing settlements associated with a contract.
    """
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.party_api = PartyAPI()
        self.registry_manager = RegistryManager()

### **Sale Settlements**

    @extend_schema(
        tags=["Sale Contracts"],
        responses={status.HTTP_200_OK: SaleSettlementSerializer(many=True)},
        summary="List Sale Contract Settlements",
        description="Retrieve a list of settlements associated with a sale contract.",
    )
    def list_sale_settlements(self, request, contract_idx=None):
        return self._list_settlements(request, contract_type="sale", contract_idx=contract_idx)

    @extend_schema(
        tags=["Sale Contracts"],
        request=SaleSettlementSerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Create Sale Contract Settlements",
        description="Add settlements to a sale contract.",
    )
    def create_sale_settlements(self, request, contract_idx=None):
        return self._create_settlements(request, contract_type="sale", contract_idx=contract_idx)

    @extend_schema(
        tags=["Sale Contracts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Sale Settlements",
        description="Delete all settlements from a sale contract.",
    )
    def destroy_sale_settlements(self, request, contract_idx=None):
        return self._destroy_settlements(request, contract_type="sale", contract_idx=contract_idx)

### **Advance Settlements**

    @extend_schema(
        tags=["Advance Contracts"],
        responses={status.HTTP_200_OK: AdvanceSettlementSerializer(many=True)},
        summary="List Advance Settlements",
        description="Retrieve a list of settlements associated with an advance contract.",
    )
    def list_advance_settlements(self, request, contract_idx=None):
        return self._list_settlements(request, contract_type="advance", contract_idx=contract_idx)

    @extend_schema(
        tags=["Advance Contracts"],
        request=AdvanceSettlementSerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Create Advance Settlements",
        description="Add settlements to an advance contract.",
    )
    def create_advance_settlements(self, request, contract_idx=None):
        return self._create_settlements(request, contract_type="advance", contract_idx=contract_idx)

    @extend_schema(
        tags=["Advance Contracts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Advance Settlements",
        description="Delete all settlements from an advance contract.",
    )
    def destroy_advance_settlements(self, request, contract_idx=None):
        return self._destroy_settlements(request, contract_type="advance", contract_idx=contract_idx)

### **Core Functions**

    def _list_settlements(self, request, contract_type=None, contract_idx=None):
        """
        Retrieve settlements for a given contract.
        """
        log_info(self.logger, f"Fetching settlements for {contract_type}:{contract_idx}.")

        try:
            contract_api = self.registry_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.registry_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            api_key = request.auth.get("api_key")
            response = self.party_api.get_parties(contract_type, int(contract_idx))

            if response["status"] == status.HTTP_200_OK:
                parties = response["data"]
            else:
                return Response({"error": response["message"]}, response["status"])

            settlement_api = self.registry_manager.get_settlement_api(contract_type)
            response = settlement_api.get_settlements(contract_type, int(contract_idx), api_key, parties)

            if response["status"] == status.HTTP_200_OK:
                serializer_class = self.registry_manager.get_settlement_serializer(contract_type)
                serializer = serializer_class(response["data"], many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": response["message"]}, response["status"])

        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_settlements(self, request, contract_type=None, contract_idx=None):
        """
        Add settlements to a contract.
        """
        log_info(self.logger, f"Adding settlements for {contract_type}:{contract_idx}.")
        self._validate_master_key(request.auth)

        try:
            contract_api = self.registry_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.registry_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            serializer_class = self.registry_manager.get_settlement_serializer(contract_type)
            log_info(self.logger, f"Using serializer class {serializer_class}")

            validated_data = self._validate_request_data(serializer_class, request.data, many=True)
            log_info(self.logger, f"Sending data to validate {validated_data}")
            self._validate_settlements(validated_data)

            settlement_api = self.registry_manager.get_settlement_api(contract_type)
            log_info(self.logger, f"Sending contract_type {contract_type}, contract_idx {contract_idx}, validated_data {validated_data}")
            response = settlement_api.add_settlements(contract_type, contract_idx, validated_data)

            if response["status"] == status.HTTP_201_CREATED:
                return Response(response["data"], status=status.HTTP_201_CREATED)
            else:
                return Response({"error": response["message"]}, response["status"])

        except PermissionDenied as pd:
            log_error(self.logger, f"Permission denied for contract {contract_idx}: {pd}")
            return Response({"detail": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _destroy_settlements(self, request, contract_type=None, contract_idx=None):
        """
        Delete all settlements associated with a contract.
        """
        log_info(self.logger, f"Deleting settlements for {contract_type}:{contract_idx}.")

        try:
            self._validate_master_key(request.auth)
            contract_api = self.registry_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.registry_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            settlement_api = self.registry_manager.get_settlement_api(contract_type)
            response = settlement_api.delete_settlements(contract_type, contract_idx)

            if response["status"] == status.HTTP_204_NO_CONTENT:
                return Response(response["data"], status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": response["message"]}, response["status"])

        except PermissionDenied as pd:
            log_error(self.logger, f"Permission denied for {contract_type}:{contract_idx}: {pd}")
            return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)