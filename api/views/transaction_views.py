from datetime import datetime

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.transaction_serializer import TransactionSerializer

from packages.api_interface import get_contract
from packages.api_interface import get_contract_transactions, add_transactions, delete_transactions

from packages.check_privacy import is_master_key

from api.permissions import HasCustomAPIKey
from api.authentication import CustomAPIKeyAuthentication

class TransactionViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication, CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Transactions"],
        parameters=[
            OpenApiParameter(name='transact_min_dt', description='Minimum transaction date for filtering (ISO 8601 format)', required=False, type=str),
            OpenApiParameter(name='transact_max_dt', description='Maximum transaction date for filtering (ISO 8601 format)', required=False, type=str),
        ],
        responses={status.HTTP_200_OK: TransactionSerializer(many=True)},
        summary="List Transactions",
        description="Retrieve a list of transactions associated with a contract"
    )
    def list_contract(self, request, contract_idx=None):
        transact_min_dt_str = request.query_params.get('transact_min_dt')
        transact_max_dt_str = request.query_params.get('transact_max_dt')

        # Convert the string dates to datetime objects, if provided
        transact_min_dt, transact_max_dt = None, None
        
        if transact_min_dt_str:
            try:
                transact_min_dt = datetime.fromisoformat(transact_min_dt_str)
            except ValueError:
                return Response("Invalid format for transact_min_dt. Expected ISO 8601 format.", status=status.HTTP_400_BAD_REQUEST)
        
        if transact_max_dt_str:
            try:
                transact_max_dt = datetime.fromisoformat(transact_max_dt_str)
            except ValueError:
                return Response("Invalid format for transact_max_dt. Expected ISO 8601 format.", status=status.HTTP_400_BAD_REQUEST)
        
        try:
            transactions = get_contract_transactions(
                int(contract_idx), 
                transact_min_dt=transact_min_dt, 
                transact_max_dt=transact_max_dt
            )
            return Response(transactions, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=['Transactions'],
        request=TransactionSerializer(many=True),
        responses={status.HTTP_201_CREATED: int},
        summary="Create Transactions",
        description="Add a list of transactions to an existing contract",
    )
    def add(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        serializer = TransactionSerializer(data=request.data, many=True)
        if serializer.is_valid():
            try:
                transact_logic = get_contract(contract_idx)['transact_logic']
                response = add_transactions(contract_idx, transact_logic, serializer.validated_data)
                return Response(response, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)   

    @extend_schema(
        tags=["Transactions"],
        responses={status.HTTP_204_NO_CONTENT: int},
        summary="Delete Transactions",
        description="Delete all transactions from a contract",
    )
    def delete_contract(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        try:
            response = delete_transactions(contract_idx)
            return Response(response, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)