from datetime import datetime, timedelta

from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.ticket_serializer import TicketSerializer

from packages.api_interface import get_contract_tickets

from packages.check_privacy import is_master_key

from api.permissions import HasCustomAPIKey
from api.authentication import CustomAPIKeyAuthentication

class TicketViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication, CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

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
            tickets = get_contract_tickets(contract_idx, start_date, end_date)
            return Response(tickets, status=status.HTTP_200_OK)
        except ValueError:
            return Response("Invalid date format. Expected ISO 8601 format.", status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Tickets"],
        responses={status.HTTP_200_OK: str},
        summary="Update Tickets on Host", 
        description="Process tickets on the host system when they have been paid"
    )
    @action(detail=True, methods=['post'], url_path='process')
    def process(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        try:
            pass
            #return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)