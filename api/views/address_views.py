from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema
import logging

from api.models.configuration_models import Configuration
from api.permissions import HasCustomAPIKey
from api.authentication import CustomAPIKeyAuthentication

logger = logging.getLogger(__name__)

class AddressViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication, CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Address"], 
        summary="Get Contract Address",
        description="Retrieve the current active contract address"
    )
    def get(self, request):
        try:
            config_entry = Configuration.objects.get(key='contract_addr')
            return Response({'contract_addr': config_entry.value}, status=status.HTTP_200_OK)
        except Configuration.DoesNotExist:
            logger.warning('Configuration key "contract_addr" does not exist.')
            return Response({'error': 'Configuration key "contract_addr" does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unexpected error retrieving contract address: {e}")
            return Response({'error': 'An unexpected error occurred while retrieving the contract address.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)