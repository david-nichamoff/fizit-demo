from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema
import logging

from api.serializers.party_serializer import PartySerializer

from packages.api_interface import get_parties, add_parties, delete_parties, delete_party
from packages.check_privacy import is_master_key

logger = logging.getLogger(__name__)

class PartyViewSet(viewsets.ViewSet):

    @extend_schema(
        tags=["Parties"],
        request=PartySerializer(many=True),
        responses={status.HTTP_200_OK: PartySerializer(many=True)},
        summary="List Parties",
        description="Retrieve a list of parties associated with a contract"
    )
    def list(self, request, contract_idx=None):
        try:
            parties = get_parties(int(contract_idx))
            return Response(parties, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving parties for contract {contract_idx}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Parties"],
        request=PartySerializer(many=True),
        responses={status.HTTP_201_CREATED: int},
        summary="Create Parties",
        description="Add a list of parties to an existing contract",
    )
    def add(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        serializer = PartySerializer(data=request.data, many=True)
        if serializer.is_valid():
            try:
                response = add_parties(contract_idx, serializer.validated_data)
                return Response(response, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error adding parties to contract {contract_idx}: {e}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.warning(f"Invalid party data for contract {contract_idx}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Parties"],
        responses={status.HTTP_204_NO_CONTENT: int},
        summary="Delete Parties",
        description="Delete all parties from a contract",
    )
    def delete_contract(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        try:
            response = delete_parties(contract_idx)
            return Response(response, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting parties for contract {contract_idx}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Parties"],
        responses={status.HTTP_204_NO_CONTENT: int},
        summary="Delete Party",
        description="Delete a party from a contract",
    )
    def delete(self, request, contract_idx=None, party_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        try:
            response = delete_party(contract_idx, party_idx)
            return Response(response, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting party {party_idx} for contract {contract_idx}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)