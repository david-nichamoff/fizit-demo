import logging

from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.recipient_serializer import RecipientSerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey

from api.interfaces import RecipientAPI

class RecipientViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.recipient_api = RecipientAPI()
        self.authenticator = AWSSecretsAPIKeyAuthentication()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

    @extend_schema(
        tags=["Accounts"],
        parameters=[
            OpenApiParameter(name='bank', description='Funding bank', required=True, default='mercury', type=str)
        ],
        responses={status.HTTP_200_OK: RecipientSerializer(many=True)},
        summary="List Recipients",
        description="Retrieve a list of all recipients"
    )
    def list(self, request):
        bank = request.query_params.get('bank')
        try:
            recipients = self.recipient_api.get_recipients(bank)
            serializer = RecipientSerializer(recipients, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            self.logger.error(f"Error retrieving recipients for bank '{bank}': {e}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)