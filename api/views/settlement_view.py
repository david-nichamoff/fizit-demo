import logging
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema

from api.serializers.settlement_serializer import SettlementSerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.interfaces import SettlementAPI, PartyAPI

from api.mixins.shared import ValidationMixin
from api.mixins.views import PermissionMixin

from api.utilities.logging import log_error, log_info, log_warning
from api.utilities.validation import is_valid_integer

class SettlementViewSet(viewsets.ViewSet, ValidationMixin, PermissionMixin):
    """
    A ViewSet for managing settlements associated with a contract.
    """
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.settlement_api = SettlementAPI()
        self.party_api = PartyAPI()

    @extend_schema(
        tags=["Settlements"],
        responses={status.HTTP_200_OK: SettlementSerializer(many=True)},
        summary="List Settlements",
        description="Retrieve a list of settlements associated with a contract.",
    )
    def list(self, request, contract_idx=None):
        """
        Retrieve settlements for a given contract.
        """
        log_info(self.logger, f"Fetching settlements for contract {contract_idx}.")

        try:
            # Validate contract_idx
            if not is_valid_integer(contract_idx):
                raise ValidationError("Contract_idx must be an integer")

            # Fetch API key and parties
            api_key = request.auth.get("api_key")

            response = self.party_api.get_parties(int(contract_idx))

            if response["status"] == status.HTTP_200_OK:
                parties = response["data"]
            else:
                return Response({"error" : response["message"]}, response["status"])

            response = self.settlement_api.get_settlements(int(contract_idx), api_key, parties)

            if response["status"] == status.HTTP_200_OK:
                # Serialize and return the data
                serializer = SettlementSerializer(response["data"], many=True)
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
        tags=["Settlements"],
        request=SettlementSerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Create Settlements",
        description="Add a list of settlements to an existing contract.",
    )
    def create(self, request, contract_idx=None):
        """
        Add settlements to a contract.
        """
        log_info(self.logger, f"Adding settlements for contract {contract_idx}.")
        self._validate_master_key(request.auth)

        try:
            # Validate contract_idx
            if not is_valid_integer(contract_idx):
                raise ValidationError("Contract_idx must be an integer")

            # Validate request data
            validated_data = self._validate_request_data(SettlementSerializer, request.data, many=True)
            response = self.settlement_api.add_settlements(contract_idx, validated_data)

            if response["status"] == status.HTTP_201_CREATED:
                # Serialize and return the data
                return Response(response["data"], status=status.HTTP_201_CREATED)
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
        tags=["Settlements"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Settlements",
        description="Delete all settlements from a contract.",
    )
    def destroy(self, request, contract_idx=None):
        """
        Delete all settlements associated with a contract.
        """
        log_info(self.logger, f"Deleting settlements for contract {contract_idx}.")
        self._validate_master_key(request.auth)

        try:
            # Validate contract_idx
            if not is_valid_integer(contract_idx):
                raise ValidationError("Contract_idx must be an integer")

            # Delete settlements via SettlementAPI
            response = self.settlement_api.delete_settlements(contract_idx)

            if response["status"] == status.HTTP_204_NO_CONTENT:
                # Serialize and return the data
                return Response(response["data"], status=status.HTTP_204_NO_CONTENT)
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