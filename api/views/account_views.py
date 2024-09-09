import logging

from rest_framework.response import Response
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.account_serializer import AccountSerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey

from api.interfaces import AccountAPI

class AccountViewSet(viewsets.ViewSet):
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, **kwargs):
        """Initialize the view with AccountAPI instance."""
        super().__init__(**kwargs)

        self.account_api = AccountAPI()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

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
            accounts = self.account_api.get_accounts(bank)
            return Response(accounts, status=status.HTTP_200_OK)
        except ValueError as ve:
            self.logger.warning(f"ValueError: {ve}")
            return Response({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)