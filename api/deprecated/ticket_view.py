import logging
from datetime import datetime, timedelta

from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.ticket_serializer import TicketSerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.interfaces import TicketAPI


class TicketViewSet(viewsets.ViewSet):
    """
    A ViewSet for managing tickets associated with a contract.
    """
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.ticket_api = TicketAPI()

    @extend_schema(
        tags=["Tickets"],
        parameters=[
            OpenApiParameter(
                name='start_date',
                description='Start date for filtering tickets (ISO 8601 format)',
                required=True,
                type=str,
                default=(datetime.now() - timedelta(days=1)).isoformat(),
            ),
            OpenApiParameter(
                name='end_date',
                description='End date for filtering tickets (ISO 8601 format)',
                required=True,
                type=str,
                default=(datetime.now() - timedelta(days=1)).isoformat(),
            ),
        ],
        responses={status.HTTP_200_OK: TicketSerializer(many=True)},
        summary="List Tickets from Host",
        description="Retrieve a list of all tickets associated with a contract from the host."
    )
    def list(self, request, contract_idx=None):
        """
        Retrieve tickets for a given contract within a date range.
        """
        start_date, end_date = self._parse_dates(
            request.query_params.get('start_date'),
            request.query_params.get('end_date')
        )

        if not start_date or not end_date:
            return self._handle_error("Invalid date format. Expected ISO 8601 format.", status.HTTP_400_BAD_REQUEST)

        try:
            self.log_info(logger, f"Fetching tickets for contract {contract_idx} from {start_date} to {end_date}.")
            tickets = self.ticket_api.get_tickets(contract_idx, start_date, end_date)
            serializer = TicketSerializer(tickets, many=True)
            self.log_info(logger, f"Successfully retrieved tickets for contract {contract_idx}.")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return self._handle_error(f"Error retrieving tickets for contract {contract_idx}: {e}", status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=["Tickets"],
        responses={status.HTTP_200_OK: str},
        summary="Process Tickets on Host",
        description="Process tickets on the host system when they have been paid."
    )
    def process(self, request, contract_idx=None):
        """
        Process tickets on the host system.
        """
        if not self._has_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")

        try:
            self.log_info(logger, f"Processing tickets for contract {contract_idx}.")
            response = self.ticket_api.process_tickets(contract_idx)
            self.log_info(logger, f"Successfully processed tickets for contract {contract_idx}.")
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return self._handle_error(f"Error processing tickets for contract {contract_idx}: {e}", status.HTTP_400_BAD_REQUEST)

    def _parse_dates(self, start_date_str, end_date_str):
        """
        Parse the start and end dates from strings to datetime objects.
        """
        try:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
            return start_date, end_date
        except (ValueError, TypeError) as e:
            self.log_warning(logger, f"Invalid date format: {e}")
            return None, None

    def _has_master_key(self, request):
        """
        Check if the provided authentication info includes the master key.
        """
        return request.auth.get('is_master_key', False)

    def _handle_error(self, message, status_code):
        """
        Handle errors consistently with logging and response.
        """
        self.log_error(logger, message)
        return Response({"error": message}, status=status_code)