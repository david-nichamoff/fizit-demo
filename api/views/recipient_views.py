from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.recipient_serializer import RecipientSerializer

from packages.api_interface import get_recipients

from api.permissions import HasCustomAPIKey
from api.authentication import CustomAPIKeyAuthentication

class RecipientViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

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
            recipients = get_recipients(bank)
            serializer = RecipientSerializer(recipients, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)