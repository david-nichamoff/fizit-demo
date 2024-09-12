import logging
from dateutil import parser as date_parser
from datetime import datetime
from datetime import timezone

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.transaction_serializer import TransactionSerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey

from api.interfaces import TransactionAPI, ContractAPI

class TransactionViewSet(viewsets.ViewSet):
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.transaction_api = TransactionAPI()
        self.contract_api = ContractAPI()
        self.authenticator = AWSSecretsAPIKeyAuthentication()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

        from datetime import datetime

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
    def list(self, request, contract_idx=None):
        self.logger.info(f"Fetching transactions for contract {contract_idx}")
        transact_min_dt_str = request.query_params.get('transact_min_dt')
        transact_max_dt_str = request.query_params.get('transact_max_dt')
        transact_min_dt, transact_max_dt = None, None
        
        if transact_min_dt_str:
            try:
                transact_min_dt = date_parser.isoparse(transact_min_dt_str).astimezone(timezone.utc)
            except ValueError:
                self.logger.warning("Invalid transact_min_dt format")
                return Response({"error": "Invalid format for transact_min_dt. Expected ISO 8601 format."}, status=status.HTTP_400_BAD_REQUEST)
        
        if transact_max_dt_str:
            try:
                transact_max_dt = date_parser.isoparse(transact_max_dt_str).astimezone(timezone.utc)
            except ValueError:
                self.logger.warning("Invalid transact_max_dt format")
                return Response({"error": "Invalid format for transact_max_dt. Expected ISO 8601 format."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            self.logger.info(f"Fetching transactions from {transact_min_dt} to {transact_max_dt}")
            transactions = self.transaction_api.get_transactions(
                int(contract_idx), 
                transact_min_dt=transact_min_dt, 
                transact_max_dt=transact_max_dt
            )
            self.logger.info(f"Successfully retrieved transactions for contract {contract_idx}")
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            self.logger.error(f"Error fetching transactions for contract {contract_idx}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=['Transactions'],
        request=TransactionSerializer(many=True),
        responses={status.HTTP_201_CREATED: int},
        summary="Create Transactions",
        description="Add a list of transactions to an existing contract",
    )
    def add(self, request, contract_idx=None):
        auth_info = request.auth  # This is where the authentication info is stored
        
        if not auth_info.get('is_master_key', False):  # Check if the master key was provided
            raise PermissionDenied("You do not have permission to perform this action.")

        self.logger.info(f"Attempting to add transactions for contract {contract_idx}")
        serializer = TransactionSerializer(data=request.data, many=True)
        if serializer.is_valid():
            try:
                self.logger.info(f"Validated transactions for contract {contract_idx}")
                transact_logic = self.contract_api.get_contract(contract_idx)['transact_logic']
                response = self.transaction_api.add_transactions(contract_idx, transact_logic, serializer.validated_data)
                self.logger.info(f"Successfully added transactions for contract {contract_idx}")
                return Response(response, status=status.HTTP_201_CREATED)
            except Exception as e:
                self.logger.error(f"Error adding transactions for contract {contract_idx}: {e}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            self.logger.warning(f"Invalid transaction data for contract {contract_idx}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)   

    @extend_schema(
        tags=["Transactions"],
        responses={status.HTTP_204_NO_CONTENT: int},
        summary="Delete Transactions",
        description="Delete all transactions from a contract",
    )
    def delete_contract(self, request, contract_idx=None):
        auth_info = request.auth  # This is where the authentication info is stored
        
        if not auth_info.get('is_master_key', False):  # Check if the master key was provided
            raise PermissionDenied("You do not have permission to perform this action.")

        self.logger.info(f"Attempting to delete transactions for contract {contract_idx}")

        try:
            response = self.transaction_api.delete_transactions(contract_idx)
            self.logger.info(f"Successfully deleted transactions for contract {contract_idx}")
            return Response(response, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            self.logger.error(f"Error deleting transactions for contract {contract_idx}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)