import logging

from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework import viewsets, status

from drf_spectacular.utils import extend_schema

from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.views.mixins.validation import ValidationMixin
from api.views.mixins.permission import PermissionMixin
from api.registry import RegistryManager
from api.config import ConfigManager
from api.interfaces import PartyAPI
from api.serializers import ListContractSerializer, PurchaseContractSerializer, SaleContractSerializer, AdvanceContractSerializer
from api.utilities.logging import log_info, log_error, log_warning

class ContractViewSet(viewsets.ViewSet, ValidationMixin, PermissionMixin):
    """
    A ViewSet for managing contract-related operations.
    """
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.party_api = PartyAPI()
        self.registry_manager = RegistryManager()
        self.config_manager = ConfigManager()
        self.logger = logging.getLogger(__name__)

    @extend_schema(
        tags=["Contracts"],
        parameters=[],
        responses={status.HTTP_200_OK: ListContractSerializer(many=True)},
        summary="List Contracts",
        description="Retrieve a list of all contracts.",
    )
    def list_contracts(self, request):
        """Retrieve a list of contracts from the underlying contract API."""
        log_info(self.logger, "Fetching contract list.")

        try:
            contract_types = self.registry_manager.get_contract_types()
            contracts = []

            for contract_type in contract_types:
                contract_api = self.registry_manager.get_contract_api(contract_type)

                # Retrieve contract count (caching is handled inside)
                response = contract_api.get_contract_count(contract_type)
                if response["status"] != status.HTTP_200_OK:
                    log_error(self.logger, f"Failed to retrieve contract count for {contract_type}")
                    continue

                contract_count = response["data"]["count"]

                # Retrieve each contract (caching is handled inside)
                for contract_idx in range(contract_count):
                    response = contract_api.get_contract(contract_type, contract_idx, request.auth.get("api_key"))

                    if response["status"] == status.HTTP_200_OK:
                        contract = {
                            "contract_type": contract_type,
                            "contract_idx": contract_idx,
                            "contract_name": response["data"].get("contract_name"),
                            "is_active": response["data"].get("is_active", True),
                            "is_quote": response["data"].get("is_quote", False),
                            "transact_logic": response["data"].get("transact_logic", {}),
                        }
                        contracts.append(contract)

            return Response(contracts, status=status.HTTP_200_OK)

        except Exception as e:
            log_error(self.logger, f"Error retrieving contract list: {e}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

### **Purchase Contracts**
    
    @extend_schema(
        tags=["Purchase Contracts"],
        request=PurchaseContractSerializer(many=False),
        responses={status.HTTP_201_CREATED: int},
        summary="Create Purchase Contract",
        description="Create a new purchase contract"
    )
    def create_purchase_contract(self, request):
        return self._create_contract(request, contract_type="purchase")

    @extend_schema(
        tags=["Purchase Contracts"],
        responses={status.HTTP_200_OK: None},
        summary="Retrieve Purchase Contract",
        description="Retrieve details of a specific purchase contract"
    )
    def retrieve_purchase_contract(self, request, contract_idx=None):
        log_info(self.logger, "test")
        return self._retrieve_contract(request, contract_type="purchase", contract_idx=contract_idx)

    @extend_schema(
        tags=["Purchase Contracts"],        
        request=PurchaseContractSerializer(many=False),
        responses={status.HTTP_200_OK: int},
        summary="Update Purchase Contract",
        description="Update specific fields of an existing purchase contract"
    )
    def update_purchase_contract(self, request, contract_idx=None):
        return self._update_contract(request, contract_type="purchase", contract_idx=contract_idx)

    @extend_schema(
        tags=["Purchase Contracts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Purchase Contract",
        description="Delete a specific purchase contract"
    )
    def destroy_purchase_contract(self, request, contract_idx=None):
        return self._destroy_contract(request, contract_type="purchase", contract_idx=contract_idx)

    @extend_schema(
        tags=["Purchase Contracts"],
        summary="Count Purchase Contracts",
        description="retrieve the total number of purchase contracts",
        responses={status.HTTP_200_OK: int}
    )
    def count_purchase_contract(self, request):
        return self._count_contract(request, contract_type="purchase")

 
### **Sale Contracts**

    @extend_schema(
        tags=["Sale Contracts"],
        request=SaleContractSerializer(many=False),
        responses={status.HTTP_201_CREATED: int},
        summary="Create Sale Contract",
        description="Create a new sale contract."
    )
    def create_sale_contract(self, request):
        return self._create_contract(request, contract_type="sale")

    @extend_schema(
        tags=["Sale Contracts"],
        responses={status.HTTP_200_OK: None},
        summary="Retrieve Sale Contract",
        description="Retrieve details of a specific sale contract"
    )
    def retrieve_sale_contract(self, request, contract_idx=None):
        return self._retrieve_contract(request, contract_type="sale", contract_idx=contract_idx)

    @extend_schema(
        tags=["Sale Contracts"],        
        request=SaleContractSerializer(many=False),
        responses={status.HTTP_200_OK: int},
        summary="Update Sale Contract",
        description="Update specific fields of an existing sale contract"
    )
    def update_sale_contract(self, request, contract_idx=None):
        return self._update_contract(request, contract_type="sale", contract_idx=contract_idx)

    @extend_schema(
        tags=["Sale Contracts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Sale Contract",
        description="Delete a specific sale contract"
    )
    def destroy_sale_contract(self, request, contract_idx=None):
        return self._destroy_contract(request, contract_type="sale", contract_idx=contract_idx)

    @extend_schema(
        tags=["Sale Contracts"],
        summary="Count Sale Contracts",
        description="Retrieve the total number of sales contracts",
        responses={status.HTTP_200_OK: int}
    )
    def count_sale_contract(self, request):
        return self._count_contract(request, contract_type="sale")

### **Advance Contracts**

    @extend_schema(
        tags=["Advance Contracts"],
        request=AdvanceContractSerializer(many=False),
        responses={status.HTTP_201_CREATED: int},
        summary="Create Advance Contract",
        description="Create a new advance contract"
    )
    def create_advance_contract(self, request):
        return self._create_contract(request, contract_type="advance")

    @extend_schema(
        tags=["Advance Contracts"],
        responses={status.HTTP_200_OK: None},
        summary="Retrieve Advance Contract",
        description="Retrieve details of a specific advance contract"
    )
    def retrieve_advance_contract(self, request, contract_idx=None):
        return self._retrieve_contract(request, contract_type="advance", contract_idx=contract_idx)

    @extend_schema(
        tags=["Advance Contracts"],        
        request=AdvanceContractSerializer(many=False),
        responses={status.HTTP_200_OK: int},
        summary="Update Advance Contract",
        description="Update specific fields of an existing advance contract"
    )
    def update_advance_contract(self, request, contract_idx=None):
        return self._update_contract(request, contract_type="advance", contract_idx=contract_idx)

    @extend_schema(
        tags=["Advance Contracts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Advance Contract",
        description="Delete a specific advance contract"
    )
    def destroy_advance_contract(self, request, contract_idx=None):
        return self._destroy_contract(request, contract_type="advance", contract_idx=contract_idx)

    @extend_schema(
        tags=["Advance Contracts"],
        summary="Count Advance Contracts",
        description="Retrieve the total number of advances contracts",
        responses={status.HTTP_200_OK: int}
    )
    def count_advance_contract(self, request, contract_idx=None):
        return self._count_contract(request, contract_type="advance")

### **Core Functions**

    def _create_contract(self, request, contract_type=None):
        log_info(self.logger, "Attempting to create a new contract.")

        try:
            self._validate_master_key(request.auth)
            self._validate_contract_type(contract_type, self.registry_manager)
            serializer_class = self.registry_manager.get_contract_serializer(contract_type)
            log_info(self.logger, f"Using serializer class {serializer_class}")

            validated_data = self._validate_request_data(serializer_class, request.data)
            log_info(self.logger, f"Sending data for validation {contract_type}: {validated_data}")
            self._validate_contract(validated_data)
            log_info(self.logger, "Contract validated")

            contract_api = self.registry_manager.get_contract_api(contract_type)
            response = contract_api.add_contract(contract_type, validated_data)

            if response["status"] == status.HTTP_201_CREATED:
                return Response(response["data"], status=status.HTTP_201_CREATED)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except PermissionDenied as pd:
            log_error(self.logger, f"Permission denied: {pd}")
            return Response({"detail": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _retrieve_contract(self, request, contract_type=None, contract_idx=None):
        log_info(self.logger, f"Fetching {contract_type}:{contract_idx}")

        try:
            contract_api = self.registry_manager.get_contract_api(contract_type)

            # Validate contract_idx
            self._validate_contract_type(contract_type, self.registry_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            parties = self.party_api.get_parties(contract_type, contract_idx)
            response = contract_api.get_contract(contract_type, contract_idx, request.auth.get("api_key"), parties["data"])

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

    def _update_contract(self, request, contract_type=None, contract_idx=None):
        log_info(self.logger, f"Updating {contract_type}:{contract_idx}")

        try:
            contract_api = self.registry_manager.get_contract_api(contract_type)

            self._validate_master_key(request.auth)
            self._validate_contract_type(contract_type, self.registry_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            parties = self.party_api.get_parties(contract_type, contract_idx)
            response = contract_api.get_contract(contract_type, contract_idx, request.auth.get("api_key"), parties["data"])

            if response["status"] != status.HTTP_200_OK:
                return Response({"error": response["message"]}, response["status"])

            contract = response["data"]
            log_info(self.logger,f"Updated contract {contract}")
            serializer_class = self.registry_manager.get_contract_serializer(contract_type)
            serializer = serializer_class(data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)

            for key, value in serializer.validated_data.items():
                contract[key] = value

            self._validate_contract(contract)
            log_info(self.logger, f"Final contract update data: {contract}")

            response = contract_api.update_contract(contract_type, contract_idx, contract)

            if response["status"] == status.HTTP_200_OK:
                return Response(response["data"], status=status.HTTP_200_OK)
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

    @extend_schema(
        tags=["Contracts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Contract",
        description="Delete a specific contract."
    )
    def _destroy_contract(self, request, contract_type=None, contract_idx=None):
        log_info(self.logger, f"Deleting {contract_type}:{contract_idx}.")

        try:
            contract_api = self.registry_manager.get_contract_api(contract_type) 

            self._validate_master_key(request.auth)
            self._validate_contract_type(contract_type, self.registry_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            response = contract_api.delete_contract(contract_type, contract_idx)
            log_info(self.logger, f"Response from delete_contract: {response}")

            if response["status"] == status.HTTP_204_NO_CONTENT:
                return Response(response["data"], status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=["Contracts"],
        summary="Contract Count",
        description="Retrieve the total number of contracts.",
        responses={status.HTTP_200_OK: int}
    )
    def _count_contract(self, request, contract_type=None):
        log_info(self.logger, f"Fetching contract count for {contract_type}")

        try:
            self._validate_contract_type(contract_type, self.registry_manager)
            contract_api = self.registry_manager.get_contract_api(contract_type) 
            response = contract_api.get_contract_count(contract_type)

            if response["status"] == status.HTTP_200_OK:
                contract_count = response["data"]["count"]
                return Response({"count": contract_count}, status=status.HTTP_200_OK)

            return Response({"error" : response["message"]}, response["status"])

        except Exception as e:
            log_error(self.logger, f"Error retrieving contract count: {e}")
            return Response({"error": f"Unexpected error {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)