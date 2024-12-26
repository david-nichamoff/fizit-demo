import logging

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema

from api.serializers.artifact_serializer import ArtifactSerializer
from api.permissions import HasCustomAPIKey
from api.authentication import AWSSecretsAPIKeyAuthentication

from api.interfaces import ArtifactAPI, ContractAPI

class ArtifactViewSet(viewsets.ViewSet):
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.artifact_api = ArtifactAPI()
        self.contract_api = ContractAPI()
        self.authenticator = AWSSecretsAPIKeyAuthentication()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  

    @extend_schema(
        tags=["Artifacts"],
        responses={status.HTTP_200_OK: ArtifactSerializer(many=True)},
        summary="List Artifacts",
        description="Retrieve a list of artifacts associated with a contract"
    )
    def list(self, request, contract_idx=None):
        try:
            artifacts = self.artifact_api.get_artifacts(int(contract_idx))
            serializer = ArtifactSerializer(artifacts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            self.logger.error(f"Error retrieving artifacts for contract {contract_idx}: {e}")
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Artifacts"],
        request={"type": "array", "items": {"type": "string", "format": "uri"}},
        responses={status.HTTP_201_CREATED: str},
        summary="Add Artifacts from URLs",
        description="Add artifacts for a contract by providing a list of URLs"
    )
    def add(self, request, contract_idx=None):
        auth_info = request.auth  # This is where the authentication info is stored

        if not auth_info.get('is_master_key', False):  # Check if the master key was provided
            raise PermissionDenied("You do not have permission to perform this action.")

        try:
            # Extract artifact URLs from the request data
            artifact_urls = request.data.get('artifact_urls', [])
            if not artifact_urls:
                raise ValueError("No artifact URLs provided in the request")

            # Pass the URLs to the ArtifactAPI to handle artifact upload
            response = self.artifact_api.add_artifacts(contract_idx, artifact_urls)
            return Response(response, status=status.HTTP_201_CREATED)

        except Exception as e:
            self.logger.error(f"Error adding artifacts for contract {contract_idx}: {e}")
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Artifacts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Artifacts",
        description="Delete all artifacts from a contract",
    )
    def delete_contract(self, request, contract_idx=None):
        auth_info = request.auth  # This is where the authentication info is stored
        
        if not auth_info.get('is_master_key', False):  # Check if the master key was provided
            raise PermissionDenied("You do not have permission to perform this action.")

        try:
            self.artifact_api.delete_artifacts(contract_idx)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            self.logger.error(f"Error deleting artifacts for contract {contract_idx}: {e}")
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)