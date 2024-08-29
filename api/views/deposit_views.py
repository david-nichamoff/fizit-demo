from datetime import datetime, timedelta
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from api.serializers.deposit_serializer import DepositSerializer
from api.permissions import HasCustomAPIKey
from api.authentication import CustomAPIKeyAuthentication
from rest_framework.exceptions import ValidationError, PermissionDenied

from packages.api_interface import get_deposits, add_deposits
from packages.check_privacy import is_master_key

class DepositViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Deposits"],
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
        summary="Get Deposit",
        description="Retrieve a list of potential bank deposits for a contract"
    )
    def list(self, request, contract_idx=None):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        try:
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)
            deposits = get_deposits(start_date, end_date, int(contract_idx))
            return Response(deposits, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response(f"Invalid date format: {str(e)}", status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Deposits"],
        request=DepositSerializer,
        responses={status.HTTP_201_CREATED: int},
        summary="Add Settlement Deposit",
        description="Add a bank deposit to a settlement period"
    )
    def add(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        serializer = DepositSerializer(data=request.data, many=True)
        if serializer.is_valid():
            try:
                response = add_deposits(int(contract_idx), serializer.validated_data)
                return Response(response, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)