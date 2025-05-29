import logging

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import viewsets, status

from drf_spectacular.utils import extend_schema

from api.serializers.artifact_serializer import ArtifactSerializer
from api.permissions import HasCustomAPIKey
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.views.mixins import ValidationMixin, PermissionMixin
from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_error, log_info, log_warning
from api.utilities.validation import is_valid_list, is_valid_url


class ArtifactViewSet(viewsets.ViewSet, ValidationMixin, PermissionMixin):
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = build_app_context()
        self.logger = logging.getLogger(__name__)

    @extend_schema(
        tags=["Contracts"],
        responses={status.HTTP_200_OK: ArtifactSerializer(many=True)},
        summary="List Artifacts",
        description="Retrieve a list of artifacts associated with a contract.",
    )
    def list_artifacts(self, request, contract_type=None, contract_idx=None):
        log_info(self.logger, f"Fetching artifacts for {contract_type} contract {contract_idx}")
        try:
            self._validate_contract_type(contract_type, self.context.domain_manager)
            contract_api = self.context.api_manager.get_contract_api(contract_type)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            api_key = request.auth.get("api_key")
            response = self.context.api_manager.get_party_api().get_parties(contract_type, int(contract_idx))
            if response["status"] == status.HTTP_200_OK:
                parties = response["data"]
            else:
                return Response({"error": response["message"]}, response["status"])

            artifact_api = self.context.api_manager.get_artifact_api()
            response = artifact_api.get_artifacts(contract_type, int(contract_idx), api_key, parties)

            if response["status"] == status.HTTP_200_OK:
                serializer = ArtifactSerializer(response["data"], many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": response["message"]}, status=response["status"])

        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @extend_schema(
        tags=["Contracts"],
        request=ArtifactSerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Add Artifacts",
        description="Add artifacts to a contract by providing a list of URLs.",
    )
    def create_artifacts(self, request, contract_type=None, contract_idx=None):
        log_info(self.logger, f"Adding artifacts for {contract_type} contract {contract_idx}")
        try:
            self._validate_master_key(request.auth)
            self._validate_contract_type(contract_type, self.context.domain_manager)
            contract_api = self.context.api_manager.get_contract_api(contract_type)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            artifact_urls = request.data
            log_info(self.logger, f"Add artifacts {artifact_urls}")

            is_valid_list(artifact_urls, allow_empty=True)
            for artifact_url in artifact_urls:
                if not is_valid_url(artifact_url):
                    raise ValidationError(f"Invalid URL: {artifact_url}")

            artifact_api = self.context.api_manager.get_artifact_api()
            response = artifact_api.add_artifacts(contract_type, int(contract_idx), artifact_urls)

            if response["status"] == status.HTTP_201_CREATED:
                log_info(self.logger, f"Successfully added artifacts for {contract_type} contract {contract_idx}")
                return Response(response["data"], status=status.HTTP_201_CREATED)
            else:
                return Response({"error": response["message"]}, status=response["status"])

        except PermissionDenied as e:
            log_error(self.logger, f"Permission denied for {contract_type} contract {contract_idx}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @extend_schema(
        tags=["Contracts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Artifacts",
        description="Delete all artifacts from a contract.",
    )
    def destroy_artifacts(self, request, contract_type=None, contract_idx=None):
        log_info(self.logger, f"Deleting artifacts for {contract_type} contract {contract_idx}")
        try:
            self._validate_master_key(request.auth)
            self._validate_contract_type(contract_type, self.context.domain_manager)
            contract_api = self.context.api_manager.get_contract_api(contract_type)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            artifact_api = self.context.api_manager.get_artifact_api()
            response = artifact_api.delete_artifacts(contract_type, int(contract_idx))

            if response["status"] == status.HTTP_204_NO_CONTENT:
                log_info(self.logger, f"Successfully deleted artifacts for {contract_type} contract {contract_idx}")
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": response["message"]}, status=response["status"])

        except PermissionDenied as e:
            log_error(self.logger, f"Permission denied for {contract_type} contract {contract_idx}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)