import logging

from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema

from api.serializers.residual_serializer import ResidualSerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey

from api.interfaces import ResidualAPI

class ResidualViewSet(viewsets.ViewSet):
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.residual_api = ResidualAPI()
        self.authenticator = AWSSecretsAPIKeyAuthentication()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

    @extend_schema(
        tags=["Residuals"],
        responses={status.HTTP_200_OK: ResidualSerializer(many=True)},
        summary="Get Residual Amounts",
        description="Get the current residual amounts for a contract as a list",
    )
    def list(self, request, contract_idx=None):
        try:
            residuals = self.residual_api.get_residuals(int(contract_idx))
            serializer = ResidualSerializer(residuals, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            self.logger.error(f"Error retrieving residuals for contract {contract_idx}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Residuals"],
        request=ResidualSerializer,
        responses={status.HTTP_201_CREATED: int},
        summary="Initiate Residual Payment",
        description="Initiate residual payment"
    )
    def add(self, request, contract_idx=None):
        auth_info = request.auth  # This is where the authentication info is stored
        
        if not auth_info.get('is_master_key', False):  # Check if the master key was provided
            raise PermissionDenied("You do not have permission to perform this action.")

        serializer = ResidualSerializer(data=request.data, many=True)
        if serializer.is_valid():
            try:
                response = self.residual_api.add_residuals(int(contract_idx), serializer.validated_data)
                return Response(response, status=status.HTTP_201_CREATED)
            except Exception as e:
                self.logger.error(f"Error initiating residual payment for contract {contract_idx}: {e}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            self.logger.warning(f"Invalid residual data for contract {contract_idx}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)