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
from api.interfaces import PartyAPI
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
        self.logger = logging.getLogger(__name__)
    
    @extend_schema(
        tags=["Contracts"],
        request=None,
        responses={status.HTTP_201_CREATED: int},
        summary="Create Contract",
        description="Create a new contract."
    )
    def create(self, request, contract_type=None):
        log_info(self.logger, "Attempting to create a new contract.")

        try:
            self._validate_master_key(request.auth)
            self._validate_contract_type(contract_type, self.registry_manager)
            log_info(self.logger, "Validation of contract type successful")

            serializer_class = self.registry_manager.get_contract_serializer(contract_type)
            log_info(self.logger, f"Using serializer class {serializer_class}")

            validated_data = self._validate_request_data(serializer_class, request.data)
            log_info(self.logger, f"Sending validated data {validated_data}")
            self._validate_contract(validated_data)

            contract_api = self.registry_manager.get_contract_api(contract_type)
            response = contract_api.add_contract(contract_type, validated_data)

            if response["status"] == status.HTTP_201_CREATED:
                return Response(response["data"], status=status.HTTP_201_CREATED)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except PermissionDenied as pd:
            log_warning(self.logger, f"Permission denied: {pd}")
            return Response({"detail": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=["Contracts"],
        responses={status.HTTP_200_OK: None},
        summary="Retrieve Contract",
        description="Retrieve details of a specific contract."
    )
    def retrieve(self, request, contract_type=None, contract_idx=None):
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

    @extend_schema(
        tags=["Contracts"],
        request=None,
        responses={status.HTTP_200_OK: int},
        summary="Update Contract",
        description="Update specific fields of an existing contract."
    )
    def update(self, request, contract_type=None, contract_idx=None):
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
            log_warning(self.logger, f"Permission denied for contract {contract_idx}: {pd}")
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
    def destroy(self, request, contract_type=None, contract_idx=None):
        log_info(self.logger, f"Deleting {contract_type}:{contract_idx}.")

        try:
            contract_api = self.registry_manager.get_contract_api(contract_type) 

            self._validate_master_key(request.auth)
            self._validate_contract_type(contract_type, self.registry_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            response = contract_api.delete_contract(contract_type, contract_idx)
            log_info(self.logger, f"Response from delete_contract: {response}")

            if response["status"] == status.HTTP_204_NO_CONTENT:
                # note that because the status is HTTP_204_NO_CONTENT, the response will 
                # always be None 
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
    def count(self, request, contract_type=None):
        log_info(self.logger, f"Fetching contract count for {contract_type}")

        try:
            self._validate_contract_type(contract_type, self.registry_manager)
            contract_api = self.registry_manager.get_contract_api(contract_type) 
            log_info(self.logger, f"Contract api: {contract_api}")

            response = contract_api.get_contract_count(contract_type)

            if response["status"] == status.HTTP_200_OK:
                return Response(response["data"], status=status.HTTP_200_OK)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except Exception as e:
            log_error(self.logger, f"Error retrieving contract count: {e}")
            return Response({"error": f"Unexpected error {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)