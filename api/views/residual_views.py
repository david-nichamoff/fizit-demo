from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.account_serializer import AccountSerializer

from packages.api_interface import pay_residual, pay_advance, get_accounts

from api.permissions import HasCustomAPIKey
from api.authentication import CustomAPIKeyAuthentication

class ResidualViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Float Accounts"],
        parameters=[
            OpenApiParameter(name='bank', description='Funding bank', required=False, type=str),
        ],
        responses={status.HTTP_200_OK: AccountSerializer(many=True)},
        summary="List Acounts",
        description="Retrieve a list of all bank accounts and balances"
    )
    def list(self, request):
        bank = request.query_params.get('bank')
        try:
            accounts = get_accounts(bank)
            return Response(accounts, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Float Accounts"],
        responses={status.HTTP_200_OK: str},
        description="Initiate residual payment"
    )
    @action(detail=True, methods=['post'], url_path='pay-residual')
    def pay_residual(self, request, contract_idx=None):
        try:
            response = pay_residual(contract_idx)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Float Accounts"],
        responses={status.HTTP_200_OK: str},
        description="Post settlement received"
    )
    @action(detail=True, methods=['post'], url_path='post-settlement')
    def post_settlement(self, request, contract_idx=None):
        try:
            # response = receive_settlement(contract_idx)
            # return Response(response, status=status.HTTP_200_OK)
            pass
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Float Accounts"],
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