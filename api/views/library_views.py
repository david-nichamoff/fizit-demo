import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.managers.library_manager import LibraryManager

class LibraryViewSet(viewsets.ViewSet):
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.library_manager = LibraryManager()
        self.logger = logging.getLogger(__name__)
        self.initialized = True

    @extend_schema(
        tags=["Library"],
        summary="Get Library Templates",
        description="Retrieve a list of library templates based on the contract type.",
        parameters=[
            OpenApiParameter(
                name="contract_type",
                description="The contract type for which templates are being requested.",
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
            )
        ],
        responses={
            200: {"type": "array", "items": {"type": "object"}},
            400: {"type": "object", "properties": {"detail": {"type": "string"}}},
            403: {"type": "object", "properties": {"detail": {"type": "string"}}},
            500: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
    )
    def list(self, request):
        auth_info = request.auth
        contract_type = request.query_params.get("contract_type")

        if not auth_info.get("is_master_key", False):
            raise PermissionDenied("You do not have permission to perform this action.")

        if not contract_type:
            return Response(
                {"detail": "The 'contract_type' query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            templates = self.library_manager.get_templates_by_contract_type(contract_type)

            return Response(
                {"templates": templates, "message": f"No templates found for contract_type: {contract_type}" if not templates else ""},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            self.logger.error(f"Error fetching library templates for {contract_type}: {e}")
            return Response(
                {"detail": "An unexpected error occurred while fetching templates."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )