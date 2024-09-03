import logging

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema

from api.serializers.settlement_serializer import SettlementSerializer
from packages.api_interface import get_settlements, add_settlements, delete_settlements
from packages.check_privacy import is_master_key
from api.permissions import HasCustomAPIKey
from api.authentication import CustomAPIKeyAuthentication

logger = logging.getLogger(__name__)

class SettlementViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication, CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Settlements"],
        responses={status.HTTP_200_OK: SettlementSerializer(many=True)},
        summary="List Settlements",
        description="Retrieve a list of settlements associated with a contract"
    )
    def list(self, request, contract_idx=None):
        try:
            settlements = get_settlements(int(contract_idx))
            logger.debug("Settlements retrieved for contract %s: %s", contract_idx, settlements)
            return Response(settlements, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving settlements for contract {contract_idx}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Settlements"],
        request=SettlementSerializer(many=True),
        responses={status.HTTP_201_CREATED: int},
        summary="Create Settlements",
        description="Add a list of settlements to an existing contract",
    )
    def add(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        serializer = SettlementSerializer(data=request.data, many=True)
        if serializer.is_valid():
            try:
                response = add_settlements(contract_idx, serializer.validated_data)
                return Response(response, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error adding settlements for contract {contract_idx}: {e}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.warning(f"Invalid settlement data for contract {contract_idx}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Settlements"],
        responses={status.HTTP_204_NO_CONTENT: int},
        summary="Delete Settlements",
        description="Delete all settlements from a contract",
    )
    def delete_contract(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        try:
            response = delete_settlements(contract_idx)
            return Response(response, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting settlements for contract {contract_idx}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)