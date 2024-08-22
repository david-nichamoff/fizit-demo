from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema

from api.serializers.artifact_serializer import ArtifactSerializer

from packages.api_interface import get_contract
from packages.api_interface import get_contract_artifacts, add_artifacts, delete_artifacts
from packages.check_privacy import is_master_key

from api.permissions import HasCustomAPIKey
from api.authentication import CustomAPIKeyAuthentication

class ArtifactViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Artifacts"],
        responses={status.HTTP_200_OK: ArtifactSerializer(many=True)},
        summary="List Artifacts",
        description="Retrieve a list of artifacts associated with a contract"
    )
    def list_contract(self, request, contract_idx=None):
        try:
            artifacts = get_contract_artifacts(int(contract_idx))
            return Response(artifacts, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Artifacts"],
        responses={status.HTTP_201_CREATED: str},
        summary="Create Artifacts",
        description="Search file system for artifacts for a contract",
    )
    def add(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        try:
            contract_name = get_contract(contract_idx)["contract_name"]
            response = add_artifacts(contract_idx, contract_name)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Artifacts"],
        responses={status.HTTP_204_NO_CONTENT: int},
        summary="Delete Artifacts",
        description="Delete all artifacts from a contract",
    )
    def delete_contract(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        try:
            response = delete_artifacts(contract_idx)
            return Response(response, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)