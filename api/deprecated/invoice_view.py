import logging
from datetime import datetime, timedelta

from rest_framework.response import Response
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.invoice_serializer import InvoiceSerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.interfaces import InvoiceAPI


class InvoiceViewSet(viewsets.ViewSet):
    """
    A ViewSet for managing invoice-related operations.
    """
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.invoice_api = InvoiceAPI()
        self.logger = logging.getLogger(__name__)

    @extend_schema(
        tags=["Invoices"],
        parameters=[
            OpenApiParameter(
                name='start_date',
                description='Start date for filtering invoices (ISO 8601 format)',
                required=True,
                type=str,
                default=(datetime.now() - timedelta(days=1)).isoformat(),
            ),
            OpenApiParameter(
                name='end_date',
                description='End date for filtering invoices (ISO 8601 format)',
                required=True,
                type=str,
                default=(datetime.now() - timedelta(days=1)).isoformat(),
            ),
        ],
        responses={status.HTTP_200_OK: InvoiceSerializer(many=True)},
        summary="List Invoices",
        description="Retrieve a list of invoices associated with a contract."
    )
    def list(self, request, contract_idx=None):
        """
        Retrieve a list of invoices filtered by date range.
        """
        self.log_info(logger, f"Retrieving invoices for contract {contract_idx} with query parameters: {request.query_params}")

        try:
            start_date, end_date = self._parse_dates(request.query_params)
            invoices = self.invoice_api.get_contract_invoices(contract_idx, start_date, end_date)
            serializer = InvoiceSerializer(invoices, many=True)
            self.log_info(logger, f"Successfully retrieved {len(serializer.data)} invoices for contract {contract_idx}.")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as ve:
            return self._handle_error("Invalid date format", ve, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return self._handle_error("Error retrieving invoices", e, status.HTTP_404_NOT_FOUND)

    def _parse_dates(self, query_params):
        """
        Parse and validate date parameters from query params.
        """
        try:
            start_date = datetime.fromisoformat(query_params.get('start_date'))
            end_date = datetime.fromisoformat(query_params.get('end_date'))
            self.logger.debug(f"Parsed start_date: {start_date}, end_date: {end_date}")
            return start_date, end_date
        except ValueError as ve:
            self.log_error(logger, f"Error parsing dates: {ve}")
            raise ValueError("Invalid date format. Expected ISO 8601 format.")

    def _handle_error(self, message, exception, status_code):
        """
        Centralized error handling and logging.
        """
        self.log_error(logger, f"{message}: {exception}")
        return Response({"error": str(exception)}, status=status_code)