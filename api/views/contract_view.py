import logging

from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema

from api.serializers.contract_serializer import ContractSerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.interfaces import ContractAPI, PartyAPI

from api.mixins.shared import ValidationMixin
from api.mixins.views import PermissionMixin

from api.utilities.logging import log_info, log_error, log_warning
from api.utilities.validation import is_valid_integer

class ContractViewSet(viewsets.ViewSet, ValidationMixin, PermissionMixin):
    """
    A ViewSet for managing contract-related operations.
    """
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.contract_api = ContractAPI()
        self.party_api = PartyAPI()
        self.logger = logging.getLogger(__name__)

    @extend_schema(
        tags=["Contracts"],
        request=ContractSerializer,
        responses={status.HTTP_201_CREATED: int},
        summary="Create Contract",
        description="Create a new contract."
    )
    def create(self, request):
        log_info(self.logger, "Attempting to create a new contract.")
        self._validate_master_key(request.auth)

        try:
            validated_data = self._validate_request_data(ContractSerializer, request.data)
            response = self.contract_api.add_contract(validated_data)

            if response["status"] == status.HTTP_201_CREATED:
                return Response(response["data"], status=status.HTTP_201_CREATED)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except PermissionDenied as pd:
            log_warning(self.logger, f"Permission denied: {pd}")
            return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=["Contracts"],
        responses={status.HTTP_200_OK: ContractSerializer(many=False)},
        summary="Retrieve Contract",
        description="Retrieve details of a specific contract."
    )
    def retrieve(self, request, contract_idx=None):
        log_info(self.logger, f"Fetching contract with ID {contract_idx}.")

        try:
            # Validate contract_idx
            if not is_valid_integer(contract_idx):
                raise ValidationError("Contract_idx must be an integer")

            parties = self.party_api.get_parties(contract_idx)
            response = self.contract_api.get_contract(contract_idx, request.auth.get("api_key"), parties["data"])

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
        request=ContractSerializer,
        responses={status.HTTP_200_OK: int},
        summary="Update Contract",
        description="Update specific fields of an existing contract."
    )
    def update(self, request, contract_idx=None):
        log_info(self.logger, f"Updating contract with ID {contract_idx}.")
        self._validate_master_key(request.auth)

        try:
            # Validate contract_idx
            if not is_valid_integer(contract_idx):
                raise ValidationError("Contract_idx must be an integer")

            parties = self.party_api.get_parties(contract_idx)
            response = self.contract_api.get_contract(contract_idx, request.auth.get("api_key"), parties["data"])

            if response["status"] != status.HTTP_200_OK:
                return Response({"error" : response["message"]}, response["status"])

            contract = response["data"]
            serializer = ContractSerializer(data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)

            for key, value in serializer.validated_data.items():
                contract[key] = value

            log_info(self.logger, f"Update contract with data {contract}")
            response = self.contract_api.update_contract(contract_idx, contract)

            if response["status"] == status.HTTP_200_OK:
                return Response(response["data"], status=status.HTTP_200_OK)
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

    @extend_schema(
        tags=["Contracts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Contract",
        description="Delete a specific contract."
    )
    def destroy(self, request, contract_idx=None):
        log_info(self.logger, f"Deleting contract with ID {contract_idx}.")
        self._validate_master_key(request.auth)

        try:
            # Validate contract_idx
            if not is_valid_integer(contract_idx):
                raise ValidationError("Contract_idx must be an integer")

            response = self.contract_api.delete_contract(contract_idx)

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
    def count(self, request):
        log_info(self.logger, "Fetching contract count.")
        try:
            response = self.contract_api.get_contract_count()

            if response["status"] == status.HTTP_200_OK:
                return Response(response["data"], status=status.HTTP_200_OK)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except Exception as e:
            log_error(self.logger, f"Error retrieving contract count: {e}")
            return Response({"error": f"Unexpected error {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)