from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from api.serializers.account_serializer import AccountSerializer
from packages.api_interface import get_accounts
from api.permissions import HasCustomAPIKey
from api.authentication import CustomAPIKeyAuthentication
import logging

logger = logging.getLogger(__name__)

class AccountViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication, CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Accounts"],
        parameters=[
            OpenApiParameter(name='bank', description='Funding bank', required=True, default='mercury', type=str),
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
        except ValueError as ve:
            logger.warning(f"ValueError: {ve}")
            return Response({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)