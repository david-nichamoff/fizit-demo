import logging

from rest_framework.response import Response
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema

from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey

from api.managers import ConfigManager

class AddressViewSet(viewsets.ViewSet):
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.config_manager = ConfigManager()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

    @extend_schema(
        tags=["Address"], 
        summary="Get Contract Address",
        description="Retrieve the current active contract address"
    )
    def get(self, request):
        try:
            config_data = self.config_manager.get_config_value('contract_addr')
            if config_data:
                return Response({'contract_addr': config_data}, status=status.HTTP_200_OK)
            else:
                self.logger.warning('Configuration key "contract_addr" does not exist.')
                return Response({'error': 'Configuration key "contract_addr" does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            self.logger.error(f"Unexpected error retrieving contract address: {e}")
            return Response({'error': 'An unexpected error occurred while retrieving the contract address.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)