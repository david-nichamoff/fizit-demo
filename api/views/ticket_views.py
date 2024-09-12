import logging

from datetime import datetime, timedelta

from rest_framework.response import Response
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.ticket_serializer import TicketSerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey

from api.interfaces import TicketAPI

class TicketViewSet(viewsets.ViewSet):
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ticket_api = TicketAPI()
        self.authenticator = AWSSecretsAPIKeyAuthentication()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

    @extend_schema(
        tags=["Tickets"],
        parameters=[
            OpenApiParameter(name='start_date', description='Start date for filtering tickets (ISO 8601 format)', required=True, type=str, default=(datetime.now() - timedelta(days=1)).isoformat()),
            OpenApiParameter(name='end_date', description='End date for filtering tickets (ISO 8601 format)', required=True, type=str, default=(datetime.now() - timedelta(days=1)).isoformat()), 
        ],
        responses={status.HTTP_200_OK: TicketSerializer(many=True)},
        summary="List Tickets from Host",
        description="Retrieve a list of all tickets associated with a contract from host"
    )
    def list(self, request, contract_idx=None):
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        try:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
            tickets = self.ticket_api.get_tickets(contract_idx, start_date, end_date)
            serializer = TicketSerializer(tickets, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError:
            return Response({"error": "Invalid date format. Expected ISO 8601 format."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
"""
    @extend_schema(
        tags=["Tickets"],
        responses={status.HTTP_200_OK: str},
        summary="Update Tickets on Host", 
        description="Process tickets on the host system when they have been paid"
    )
    @action(detail=True, methods=['post'], url_path='process')
    def process_tickets(self, request, contract_idx=None):
        auth_info = request.auth  # This is where the authentication info is stored
        
        if not auth_info.get('is_master_key', False):  # Check if the master key was provided
            raise PermissionDenied("You do not have permission to perform this action.")

        try:
            # Assuming process_tickets function processes the tickets on the host system
            response = process_tickets(contract_idx)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            """