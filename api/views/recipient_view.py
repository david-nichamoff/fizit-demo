import logging
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.recipient_serializer import RecipientSerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.interfaces import RecipientAPI

from api.mixins.shared import ValidationMixin
from api.utilities.logging import log_error, log_info


class RecipientViewSet(viewsets.ViewSet, ValidationMixin):
    """
    A ViewSet for managing recipients.
    """
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recipient_api = RecipientAPI()
        self.logger = logging.getLogger(__name__)

    @extend_schema(
        tags=["Recipients"],
        parameters=[
            OpenApiParameter(
                name='bank',
                description='Funding bank',
                required=True,
                default='mercury',
                type=str
            )
        ],
        responses={status.HTTP_200_OK: RecipientSerializer(many=True)},
        summary="List Recipients",
        description="Retrieve a list of all recipients."
    )
    def list(self, request):
        """
        Retrieve a list of recipients for the specified bank.
        """
        log_info(self.logger, f"Fetching recipients with query parameters: {request.query_params}")
        try:
            # Validate required query parameter
            bank = request.query_params.get('bank')
            self._validate_query_param("bank", bank)

            # Fetch recipients from RecipientAPI
            response = self.recipient_api.get_recipients(bank)

            if response["status"] == status.HTTP_200_OK:
                # Serialize and return the data
                serializer = RecipientSerializer(response["data"], many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)