import logging

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema

from api.serializers.advance_serializer import AdvanceSerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey

from api.interfaces import AdvanceAPI

class AdvanceViewSet(viewsets.ViewSet):
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super(AdvanceViewSet, self).__init__(*args, **kwargs)

        self.advance_api = AdvanceAPI()
        self.authenticator = AWSSecretsAPIKeyAuthentication()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

    @extend_schema(
        tags=["Advances"],
        responses={status.HTTP_200_OK: AdvanceSerializer(many=True)},
        summary="Get Advance Amounts",
        description="Get the current advance amounts for a contract as a list",
    )
    def list(self, request, contract_idx=None):
        try:
            advances = self.advance_api.get_advances(int(contract_idx))
            serializer = AdvanceSerializer(advances, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            self.logger.error(f"Error retrieving advances for contract {contract_idx}: {e}")
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Advances"],
        request=AdvanceSerializer,
        responses={status.HTTP_201_CREATED: int},
        summary="Initiate Advance Payment",
        description="Initiate advance payment"
    )
    def add(self, request, contract_idx=None):
        auth_info = request.auth  # This is where the authentication info is stored
        
        if not auth_info.get('is_master_key', False):  # Check if the master key was provided
            raise PermissionDenied("You do not have permission to perform this action.")
        
        serializer = AdvanceSerializer(data=request.data, many=True)
        if serializer.is_valid():
            try:
                response = self.advance_api.add_advances(int(contract_idx), serializer.validated_data)
                return Response(response, status=status.HTTP_201_CREATED)
            except RuntimeError as e:
                self.logger.error(f"Runtime error when adding advances for contract {contract_idx}: {e}")
                return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                self.logger.error(f"Unexpected error when adding advances for contract {contract_idx}: {e}")
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            self.logger.warning(f"Validation failed when adding advances for contract {contract_idx}: {serializer.errors}")
            return