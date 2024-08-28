from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import viewsets, status

from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.account_serializer import AccountSerializer

from packages.api_interface import get_accounts

from api.permissions import HasCustomAPIKey
from api.authentication import CustomAPIKeyAuthentication

class AccountViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Accounts"],
        parameters=[
            OpenApiParameter(name='bank', description='Funding bank', required=True, type=str),
        ],
        responses={status.HTTP_200_OK: AccountSerializer(many=True)},
        summary="List Accounts",
        description="Retrieve a list of all bank accounts and balances"
    )
    def list(self, request):
        bank = request.query_params.get('bank')
        try:
            accounts = get_accounts(bank)
            return Response(accounts, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)