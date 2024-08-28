from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.residual_serializer import ResidualSerializer
from packages.api_interface import get_residuals, add_residuals

from api.permissions import HasCustomAPIKey
from api.authentication import CustomAPIKeyAuthentication

class ResidualViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Residuals"],
        responses={status.HTTP_200_OK: ResidualSerializer(many=True)},
        summary="Get Residual Amounts",
        description="Get a the current residual amounts for a contract as a list",
    )
    def list(self, request,contract_idx=None):
        try:
            advance = get_residuals(int(contract_idx))
            return Response(advance, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Residuals"],
        responses={status.HTTP_200_OK: str},
        description="Initiate residual payment"
    )
    @action(detail=True, methods=['post'], url_path='pay-residual')
    def add(self, request, contract_idx=None):
        try:
            response = add_residual(contract_idx)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)