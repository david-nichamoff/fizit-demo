import logging

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema

from api.serializers.party_serializer import PartySerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey

from api.interfaces import PartyAPI

logger = logging.getLogger(__name__)

class PartyViewSet(viewsets.ViewSet):
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.authenticator = AWSSecretsAPIKeyAuthentication()
        self.party_api = PartyAPI()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

    @extend_schema(
        tags=["Parties"],
        request=PartySerializer(many=True),
        responses={status.HTTP_200_OK: PartySerializer(many=True)},
        summary="List Parties",
        description="Retrieve a list of parties associated with a contract"
    )
    def list(self, request, contract_idx=None):
        try:
            parties = self.party_api.get_parties(int(contract_idx))
            serializer = PartySerializer(parties, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            self.logger.error(f"Error retrieving parties for contract {contract_idx}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Parties"],
        request=PartySerializer(many=True),
        responses={status.HTTP_201_CREATED: int},
        summary="Create Parties",
        description="Add a list of parties to an existing contract",
    )
    def add(self, request, contract_idx=None):
        auth_info = request.auth  # This is where the authentication info is stored
        
        if not auth_info.get('is_master_key', False):  # Check if the master key was provided
            raise PermissionDenied("You do not have permission to perform this action.")

        serializer = PartySerializer(data=request.data, many=True)
        if serializer.is_valid():
            try:
                response = self.party_api.add_parties(contract_idx, serializer.validated_data)
                return Response(response, status=status.HTTP_201_CREATED)
            except Exception as e:
                self.logger.error(f"Error adding parties to contract {contract_idx}: {e}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            self.logger.warning(f"Invalid party data for contract {contract_idx}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Parties"],
        responses={status.HTTP_204_NO_CONTENT: int},
        summary="Delete Parties",
        description="Delete all parties from a contract",
    )
    def delete_contract(self, request, contract_idx=None):
        auth_info = request.auth  # This is where the authentication info is stored
        
        if not auth_info.get('is_master_key', False):  # Check if the master key was provided
            raise PermissionDenied("You do not have permission to perform this action.")

        try:
            response = self.party_api.delete_parties(contract_idx)
            return Response(response, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            self.logger.error(f"Error deleting parties for contract {contract_idx}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Parties"],
        responses={status.HTTP_204_NO_CONTENT: int},
        summary="Delete Party",
        description="Delete a party from a contract",
    )
    def delete(self, request, contract_idx=None, party_idx=None):
        auth_info = request.auth  # This is where the authentication info is stored
        
        if not auth_info.get('is_master_key', False):  # Check if the master key was provided
            raise PermissionDenied("You do not have permission to perform this action.")

        try:
            response = self.party_api.delete_party(contract_idx, party_idx)
            return Response(response, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            self.logger.error(f"Error deleting party {party_idx} for contract {contract_idx}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)