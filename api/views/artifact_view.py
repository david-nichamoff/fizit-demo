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

### **Purchase Artifacts**

    @extend_schema(
        tags=["Purchase Contracts"],
        responses={status.HTTP_200_OK: ArtifactSerializer(many=True)},
        summary="List Purchase Artifacts",
        description="Retrieve a list of artifacts associated with a purchase contract.",
    )
    def list_purchase_artifacts(self, request, contract_idx=None):
        return self._list_artifacts(request, "purchase", contract_idx)

    @extend_schema(
        tags=["Purchase Contracts"],
        request=ArtifactSerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Add Purchase Artifacts",
        description="Add artifacts to a purchase contract by providing a list of URLs.",
    )
    def create_purchase_artifacts(self, request, contract_idx=None):
        return self._create_artifacts(request, "purchase", contract_idx)

    @extend_schema(
        tags=["Purchase Contracts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Purchase Artifacts",
        description="Delete all artifacts from a purchase contract.",
    )
    def destroy_purchase_artifacts(self, request, contract_idx=None):
        return self._destroy_artifacts(request, "purchase", contract_idx)

### **Sale Artifacts**

    @extend_schema(
        tags=["Sale Contracts"],
        responses={status.HTTP_200_OK: ArtifactSerializer(many=True)},
        summary="List Sale Artifacts",
        description="Retrieve a list of artifacts associated with a sale contract.",
    )
    def list_sale_artifacts(self, request, contract_idx=None):
        return self._list_artifacts(request, "sale", contract_idx)

    @extend_schema(
        tags=["Sale Contracts"],
        request=ArtifactSerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Add Sale Artifacts",
        description="Add artifacts to a sale contract by providing a list of URLs.",
    )
    def create_sale_artifacts(self, request, contract_idx=None):
        return self._create_artifacts(request, "sale", contract_idx)

    @extend_schema(
        tags=["Sale Contracts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Sale Artifacts",
        description="Delete all artifacts from a sale contract.",
    )
    def destroy_sale_artifacts(self, request, contract_idx=None):
        return self._destroy_artifacts(request, "sale", contract_idx)

### **Advance Artifacts**

    @extend_schema(
        tags=["Advance Contracts"],
        responses={status.HTTP_200_OK: ArtifactSerializer(many=True)},
        summary="List Advance Artifacts",
        description="Retrieve a list of artifacts associated with an advance contract.",
    )
    def list_advance_artifacts(self, request, contract_idx=None):
        return self._list_artifacts(request, "advance", contract_idx)

    @extend_schema(
        tags=["Advance Contracts"],
        request=ArtifactSerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Add Advance Artifacts",
        description="Add artifacts to an advance contract by providing a list of URLs.",
    )
    def create_advance_artifacts(self, request, contract_idx=None):
        return self._create_artifacts(request, "advance", contract_idx)

    @extend_schema(
        tags=["Advance Contracts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Advance Artifacts",
        description="Delete all artifacts from an advance contract.",
    )
    def destroy_advance_artifacts(self, request, contract_idx=None):
        return self._destroy_artifacts(request, "advance", contract_idx)

### **Core Functions**

    def _list_artifacts(self, request, contract_type, contract_idx):
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

    def _create_artifacts(self, request, contract_type, contract_idx):
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

    def _destroy_artifacts(self, request, contract_type, contract_idx):
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