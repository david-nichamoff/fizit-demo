from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import viewsets, status
from rest_framework.exceptions import ValidationError, PermissionDenied
from drf_spectacular.utils import extend_schema

from api.serializers.residual_serializer import ResidualSerializer
from packages.api_interface import get_residuals, add_residuals
from packages.check_privacy import is_master_key

from api.permissions import HasCustomAPIKey
from api.authentication import CustomAPIKeyAuthentication

import logging

logger = logging.getLogger(__name__)

class ResidualViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Residuals"],
        responses={status.HTTP_200_OK: ResidualSerializer(many=True)},
        summary="Get Residual Amounts",
        description="Get the current residual amounts for a contract as a list",
    )
    def list(self, request, contract_idx=None):
        try:
            residuals = get_residuals(int(contract_idx))
            return Response(residuals, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving residuals for contract {contract_idx}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Residuals"],
        request=ResidualSerializer,
        responses={status.HTTP_201_CREATED: int},
        summary="Initiate Residual Payment",
        description="Initiate residual payment"
    )
    def add(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        serializer = ResidualSerializer(data=request.data, many=True)
        if serializer.is_valid():
            try:
                response = add_residuals(int(contract_idx), serializer.validated_data)
                return Response(response, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error initiating residual payment for contract {contract_idx}: {e}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.warning(f"Invalid residual data for contract {contract_idx}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)