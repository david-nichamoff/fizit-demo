import logging

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import viewsets, status

from drf_spectacular.utils import extend_schema

from api.serializers.party_serializer import PartySerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.config import ConfigManager
from api.registry import RegistryManager
from api.views.mixins.validation import ValidationMixin
from api.views.mixins.permission import PermissionMixin
from api.interfaces import PartyAPI
from api.utilities.logging import log_error, log_info, log_warning

class PartyViewSet(viewsets.ViewSet, ValidationMixin, PermissionMixin):
    """
    A ViewSet for managing parties associated with a contract.
    """
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_manager = ConfigManager()
        self.registry_manager = RegistryManager()
        self.party_api = PartyAPI()
        self.logger = logging.getLogger(__name__)

    @extend_schema(
        tags=["Parties"],
        responses={status.HTTP_200_OK: PartySerializer(many=True)},
        summary="List Parties",
        description="Retrieve a list of parties associated with a contract."
    )
    def list(self, request, contract_type=None, contract_idx=None):
        """
        Retrieve a list of parties for a given contract.
        """
        log_info(self.logger, f"Fetching parties for {contract_type}:{contract_idx}")

        try:
            contract_api = self.registry_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.registry_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            response = self.party_api.get_parties(contract_type, int(contract_idx))

            if response["status"] == status.HTTP_200_OK:
                serializer = PartySerializer(response["data"], many=True)
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
        tags=["Parties"],
        request=PartySerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Create Parties",
        description="Add a list of parties to an existing contract."
    )
    def create(self, request, contract_type=None, contract_idx=None):
        log_info(self.logger, f"Attempting to add parties to {contract_type}:{contract_idx}")

        try:
            self._validate_master_key(request.auth)
            self._validate_contract_type(contract_type, self.registry_manager)

            contract_api = self.registry_manager.get_contract_api(contract_type)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            validated_data = self._validate_request_data(PartySerializer, request.data, many=True)
            self._validate_parties(validated_data, self.config_manager)

            response = self.party_api.add_parties(contract_type, int(contract_idx), validated_data)
            log_info(self.logger, f"Successfully added parties to {contract_type}:{contract_idx}")

            if response["status"] == status.HTTP_201_CREATED:
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
        tags=["Parties"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete All Parties",
        description="Delete all parties from a contract",
        operation_id="delete_all_parties"
    )
    def destroy(self, request, contract_type=None, contract_idx=None):
        log_info(self.logger, f"Attempting to delete all parties for {contract_type}:{contract_idx}")

        try:
            contract_api = self.registry_manager.get_contract_api(contract_type)
            self._validate_master_key(request.auth)
            self._validate_contract_type(contract_type, self.registry_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            response = self.party_api.delete_parties(contract_type, int(contract_idx))

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