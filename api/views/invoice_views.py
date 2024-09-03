from datetime import datetime, timedelta
import logging

from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.invoice_serializer import InvoiceSerializer

from packages.api_interface import get_contract_invoices

from api.permissions import HasCustomAPIKey
from api.authentication import CustomAPIKeyAuthentication

logger = logging.getLogger(__name__)

class InvoiceViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication, CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

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
            invoices = get_contract_invoices(contract_idx, start_date, end_date)
            return Response(invoices, status=status.HTTP_200_OK)
        except ValueError as ve:
            logger.error(f"Invalid date format provided: {ve}")
            return Response({"error": "Invalid date format. Expected ISO 8601 format."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error retrieving invoices for contract {contract_idx}: {e}")
            return Response({"error": "An error occurred while retrieving invoices."}, status=status.HTTP_404_NOT_FOUND)