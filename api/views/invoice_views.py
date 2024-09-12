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
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.invoice_api = InvoiceAPI()
        self.authenticator = AWSSecretsAPIKeyAuthentication()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

    @extend_schema(
        tags=["Invoices"],
        parameters=[
            OpenApiParameter(name='start_date', description='Start date for filtering invoices (ISO 8601 format)', required=True, type=str, default=(datetime.now() - timedelta(days=1)).isoformat()),
            OpenApiParameter(name='end_date', description='End date for filtering invoices (ISO 8601 format)', required=True, type=str, default=(datetime.now() - timedelta(days=1)).isoformat()), 
        ],
        responses={status.HTTP_200_OK: InvoiceSerializer(many=True)},
        summary="List Invoices from Host",
        description="Retrieve a list of all invoices associated with a contract from host"
    )
    def list(self, request, contract_idx=None):
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        try:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
            invoices = self.invoice_api.get_contract_invoices(contract_idx, start_date, end_date)
            serializer = InvoiceSerializer(invoices, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as ve:
            self.logger.error(f"Invalid date format provided: {ve}")
            return Response({"error": "Invalid date format. Expected ISO 8601 format."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.logger.error(f"Error retrieving invoices for contract {contract_idx}: {e}")
            return Response({"error": "An error occurred while retrieving invoices."}, status=status.HTTP_404_NOT_FOUND)