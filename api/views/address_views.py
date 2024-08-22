from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema

from api.models.configuration_models import Configuration

from api.permissions import HasCustomAPIKey
from api.authentication import CustomAPIKeyAuthentication

class AddressViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Address"], 
        summary="Retrieves the current active contract address",
        description="Retrieve the curent active contract address"
    )
    def get(self, request):
        try:
            config_entry = Configuration.objects.get(key='contract_addr')
            return Response({'contract_addr': config_entry.value}, status=status.HTTP_200_OK)
        except Configuration.DoesNotExist:
            return Response({'error': 'Configuration key "contract_addr" does not exist.'}, status=status.HTTP_404_NOT_FOUND)