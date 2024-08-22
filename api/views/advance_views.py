from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema

from packages.api_interface import pay_advance

from api.serializers.advance_serializer import AdvanceSerializer

from api.permissions import HasCustomAPIKey
from api.authentication import CustomAPIKeyAuthentication

class AdvanceViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Advances"],
        responses={status.HTTP_200_OK: AdvanceSerializer(many=True)},
        summary="Get a the current advance amount for a contract",
        description="Get a the current advance amount for a contract",
    )
    def list(self, request):
        bank = request.query_params.get('bank')
        try:
            accounts = get_accounts(bank)
            return Response(accounts, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Advances"],
        responses={status.HTTP_200_OK: str},
        description="Initiate advance payment"
    )
    @action(detail=True, methods=['post'], url_path='pay-advance')
    def pay_advance(self, request, account_id=None):
        try:
            response = pay_advance(account_id)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)