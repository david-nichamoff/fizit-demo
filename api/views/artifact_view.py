import logging

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import viewsets, status

from drf_spectacular.utils import extend_schema

from api.serializers.artifact_serializer import ArtifactSerializer
from api.permissions import HasCustomAPIKey
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.interfaces import ArtifactAPI
from api.registry import RegistryManager
from api.views.mixins.validation import ValidationMixin
from api.views.mixins.permission import PermissionMixin
from api.utilities.logging import log_error, log_info, log_warning
from api.utilities.validation import is_valid_list, is_valid_url

class ArtifactViewSet(viewsets.ViewSet, ValidationMixin, PermissionMixin):
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        """Initialize the view with ArtifactAPI instance and logger."""
        super().__init__(*args, **kwargs)
        self.artifact_api = ArtifactAPI()
        self.registry_manager = RegistryManager()
        self.logger = logging.getLogger(__name__)

    @extend_schema(
        tags=["Artifacts"],
        responses={status.HTTP_200_OK: ArtifactSerializer(many=True)},
        summary="List Artifacts",
        description="Retrieve a list of artifacts associated with a contract.",
    )
    def list(self, request, contract_type=None, contract_idx=None):
        """Retrieve a list of artifacts for a specific contract."""
        log_info(self.logger, f"Fetching artifacts for contract {contract_type}:{contract_idx}")

        try:
            # Validate contract_type and contract_idx
            contract_api = self.registry_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.registry_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            # Fetch artifacts using ArtifactAPI
            response = self.artifact_api.get_artifacts(contract_type, int(contract_idx))

            if response["status"] == status.HTTP_200_OK:
                # Serialize and return the data
                serializer = ArtifactSerializer(response["data"], many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=["Artifacts"],
        request={"type": "array", "items": {"type": "string", "format": "uri"}},
        responses={status.HTTP_201_CREATED: dict},
        summary="Add Artifacts from URLs",
        description="Add artifacts for a contract by providing a list of URLs.",
    )
    def create(self, request, contract_type=None, contract_idx=None):
        """Add artifacts to a specific contract by providing a list of URLs."""
        log_info(self.logger, f"Adding artifacts for contract {contract_type}:{contract_idx}")

        try:
            # Validate master key and contract_idx
            self._validate_master_key(request.auth)
            contract_api = self.registry_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.registry_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            # Validate request data
            artifact_urls = request.data.get("artifact_urls", [])
            is_valid_list(artifact_urls, allow_empty=True)
    
            for artifact_url in artifact_urls:
                if not is_valid_url(artifact_url):
                    raise ValidationError(f"URL {artifact_url} is not a valid URL")

            # Add artifacts using ArtifactAPI
            response = self.artifact_api.add_artifacts(contract_type, int(contract_idx), artifact_urls)

            if response["status"] == status.HTTP_201_CREATED:
                log_info(self.logger, f"Successfully added artifacts to {contract_type}:{contract_idx}")
                return Response(response["data"], status=status.HTTP_201_CREATED)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except PermissionDenied as pd:
            log_warning(self.logger, f"Permission denied for {contract_type}:{contract_idx}: {pd}")
            return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=["Artifacts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Artifacts",
        description="Delete all artifacts from a contract.",
    )
    def destroy(self, request, contract_type=None, contract_idx=None):
        """Delete all artifacts for a specific contract."""
        log_info(self.logger, f"Deleting artifacts for {contract_type}:{contract_idx}")
        auth_info = request.auth

        try:
            # Validate master key and contract_idx
            self._validate_master_key(auth_info)

            # Validate contract_type and contract_idx
            contract_api = self.registry_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.registry_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            # Delete artifacts using ArtifactAPI
            response = self.artifact_api.delete_artifacts(contract_type, int(contract_idx))

            if response["status"] == status.HTTP_204_NO_CONTENT:
                log_info(self.logger, f"Successfully deleted artifacts for {contract_type}:{contract_idx}: {response["data"]}")
                return Response(response["data"],status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except PermissionDenied as pd:
            log_warning(self.logger, f"Permission denied for {contract_type}:{contract_idx}: {pd}")
            return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)