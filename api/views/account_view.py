import logging

from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.exceptions import ValidationError

from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.account_serializer import AccountSerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.views.mixins import ValidationMixin, PermissionMixin
from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_error, log_info, log_warning

class AccountViewSet(viewsets.ViewSet, ValidationMixin, PermissionMixin):
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, **kwargs):
        """Initialize the view with AccountAPI instance and logger."""
        super().__init__(**kwargs)
        self.context = build_app_context() 
        self.logger = logging.getLogger(__name__)

    @extend_schema(
        tags=["Bank"],
        parameters=[
            OpenApiParameter(
                name="bank",
                description="Funding bank",
                required=True,
                type=str,
                default="manual",
            )
        ],
        responses={status.HTTP_200_OK: AccountSerializer(many=True)},
        summary="List Accounts",
        description="Retrieve a list of all bank accounts and balances.",
    )
    def list(self, request):
        bank = request.query_params.get("bank")
        log_info(self.logger, f"Received request to list accounts for bank: {bank}")

        try:
            if bank not in self.context.domain_manager.get_banks():
                raise ValidationError("Invalid bank")

            self._validate_master_key(request.auth)

            log_info(self.logger, f"Getting accounts from bank {bank}")
            account_api = self.context.api_manager.get_account_api()
            response = account_api.get_accounts(bank)

            if response["status"] == status.HTTP_200_OK:
                # Serialize the data for the response
                serializer = AccountSerializer(response["data"], many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)