from datetime import datetime, timedelta
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from api.serializers.deposit_serializer import DepositSerializer
from packages.api_interface import get_deposits
from api.permissions import HasCustomAPIKey
from api.authentication import CustomAPIKeyAuthentication

class DepositViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Float Accounts"],
        parameters=[
            OpenApiParameter(
                name='start_date', 
                description='Start date for filtering deposits in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)', 
                required=True, 
                type=str, 
                default=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
            ),
            OpenApiParameter(
                name='end_date', 
                description='End date for filtering deposits in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)', 
                required=True, 
                type=str, 
                default=datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            ),
        ],
        responses={status.HTTP_200_OK: DepositSerializer(many=True)},
        summary="List Deposits",
        description="Retrieve a list of all pending bank deposits"
    )
    def list(self, request, account_id=None):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        try:
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)
            deposits = get_deposits(start_date, end_date, account_id)
            serializer = DepositSerializer(deposits, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response(f"Invalid date format: {str(e)}", status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)