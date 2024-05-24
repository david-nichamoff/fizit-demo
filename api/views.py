from datetime import datetime, timedelta

from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .serializers import ContractSerializer, SettlementSerializer, TransactionSerializer
from .serializers import ArtifactSerializer, AccountSerializer, RecipientSerializer
from .serializers import DepositSerializer

from packages.interface import get_contracts, add_contract, update_contract
from packages.interface import get_settlements, add_settlements, delete_settlements
from packages.interface import get_transactions, add_transactions, delete_transactions
from packages.interface import pay_residual, pay_advance, get_deposits
from packages.interface import get_accounts, get_recipients
from packages.interface import get_artifacts, add_artifacts, delete_artifacts

class ContractViewSet(viewsets.ViewSet):
    lookup_field = 'contract_idx'

    @extend_schema(
        parameters=[
            OpenApiParameter(name='contract_idx', description='Contract index', required=False, type=str),
            OpenApiParameter(name='bank', description='Funding bank', required=False, type=str),
            OpenApiParameter(name='account_ids', description='Funding account_id list, comma separated ', required=False, type=str)
        ],
        responses={status.HTTP_200_OK: ContractSerializer(many=True)},
        description="Get contracts"
    )
    def list(self, request):
        contract_idx = request.query_params.get('contract_idx')
        bank = request.query_params.get('bank')
        account_ids = request.query_params.get('account_id')
        if account_ids is not None: account_ids = [account_ids]
        if contract_idx is not None: contract_idx = int(contract_idx)

        try:
            contracts = get_contracts(contract_idx, bank, account_ids)
            serializer = ContractSerializer(contracts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        request=ContractSerializer,
        responses={status.HTTP_201_CREATED: int},
        description="Create a new contract"
    )
    def create(self, request):
        serializer = ContractSerializer(data=request.data)
        if serializer.is_valid():
            contract_dict = serializer.validated_data 
            try:
                contract_idx = add_contract(contract_dict)
                return Response(contract_idx, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    @extend_schema(
        request=ContractSerializer,
        responses={status.HTTP_200_OK: int},
        description="Partial update of an existing contract"
    )
    def partial_update(self, request, contract_idx=None):
        try:
            contract_dict = get_contracts(contract_idx)
            serializer = ContractSerializer(data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            for key, value in serializer.validated_data.items():
                contract_dict[key] = value

            response = update_contract(contract_idx, contract_dict)
            return Response(response, status=status.HTTP_200_OK)

        except ValidationError as ve:
            return Response(ve.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        responses={status.HTTP_200_OK: str},
        description="Initiate advance payment"
    )
    @action(detail=True, methods=['post'], url_path='pay-advance')
    def pay_advance(self, request, contract_idx=None):
        try:
            response = pay_advance(contract_idx)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={status.HTTP_200_OK: str},
        description="Initiate residual payment"
    )
    @action(detail=True, methods=['post'], url_path='pay-residual')
    def pay_residual(self, request, contract_idx=None):
        try:
            response = pay_residual(contract_idx)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={status.HTTP_200_OK: str},
        description="Post settlement received"
    )
    @action(detail=True, methods=['post'], url_path='post-settlement')
    def post_settlement(self, request, contract_idx=None):
        try:
            # response = receive_settlement(contract_idx)
            # return Response(response, status=status.HTTP_200_OK)
            pass
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class SettlementViewSet(viewsets.ViewSet):

    @extend_schema(
        parameters = [
            OpenApiParameter(name='contract_idx', description='Contract index', required=False, type=str),
            OpenApiParameter(name='bank', description='Funding bank', required=False, type=str),
            OpenApiParameter(name='account_ids', description='Funding account_id list, comma separated ', required=False, type=str)
        ],
        responses={status.HTTP_200_OK: SettlementSerializer(many=True)},
        description="List settlements"
    )
    def list(self, request):
        contract_idx = request.query_params.get('contract_idx')
        bank = request.query_params.get('bank')
        account_ids = request.query_params.get('account_id')
        if contract_idx is not None: contract_idx = int(contract_idx)
        if account_ids is not None: account_ids = [account_ids]
        
        try:
            settlements = get_settlements(contract_idx, bank, account_ids)
            return Response(settlements, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        request=SettlementSerializer,
        responses={status.HTTP_201_CREATED: int},
        description="Add a list of settlements to an existing contract"
    )
    def create(self, request, contract_idx=None):
        serializer = SettlementSerializer(data=request.data, many=True)
        if serializer.is_valid():
            try:
                response = add_settlements(contract_idx, serializer.validated_data)
                return Response(response, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)   

    @extend_schema(
        responses={status.HTTP_204_NO_CONTENT: int},
        description="Delete all settlements from a contract"
    )
    def delete(self, request, contract_idx=None):
        try:
            response = delete_settlements(contract_idx)
            return Response(response, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

class TransactionViewSet(viewsets.ViewSet):

    @extend_schema(
        parameters = [
            OpenApiParameter(name='contract_idx', description='Contract index', required=False, type=str),
            OpenApiParameter(name='bank', description='Funding bank', required=False, type=str),
            OpenApiParameter(name='account_ids', description='Funding account_id list, comma separated ', required=False, type=str)
        ],
        responses={status.HTTP_200_OK: TransactionSerializer(many=True)},
        description="List all transactions"
    )
    def list(self, request):
        contract_idx = request.query_params.get('contract_idx')
        bank = request.query_params.get('bank')
        account_ids = request.query_params.get('account_ids')
        if contract_idx is not None: contract_idx = int(contract_idx)
        if account_ids is not None: account_ids = [account_ids]

        try:
            transactions = get_transactions(contract_idx, bank, account_ids)
            return Response(transactions, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        request=TransactionSerializer,
        responses={status.HTTP_201_CREATED: int},
        description="Add a list of transactions to an existing contract"
    )
    def create(self, request, contract_idx=None):
        serializer = TransactionSerializer(data=request.data, many=True)
        if serializer.is_valid():
            try:
                transact_logic = get_contracts(contract_idx)['transact_logic']
                response = add_transactions(contract_idx, transact_logic, serializer.validated_data)
                return Response(response, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)   

    @extend_schema(
        responses={status.HTTP_204_NO_CONTENT: int},
        description="Delete all transactions from a contract"
    )
    def delete(self, request, contract_idx=None):
        try:
            response = delete_transactions(contract_idx)
            return Response(response, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

class ArtifactViewSet(viewsets.ViewSet):

    @extend_schema(
        parameters = [
            OpenApiParameter(name='contract_idx', description='Contract index', required=False, type=str)
        ],
        responses={status.HTTP_200_OK: ArtifactSerializer(many=True)},
        description="List all artifacts for a contract"
    )
    def list(self, request):
        contract_idx = int(request.query_params.get('contract_idx'))
        if contract_idx is not None: contract_idx = int(contract_idx)

        try:
            artifacts = get_artifacts(contract_idx)
            return Response(artifacts, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        responses={status.HTTP_201_CREATED: str},
        description="Search file system for artifacts for a contract"
    )
    def create(self, request, contract_idx=None):
        try:
            contract_name = get_contracts(contract_idx)["contract_name"]
            response = add_artifacts(contract_idx, contract_name)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={status.HTTP_204_NO_CONTENT: int},
        description="Delete all artifacts from a contract"
    )
    def delete(self, request, contract_idx=None):
        try:
            response = delete_artifacts(contract_idx)
            return Response(response, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

class AccountViewSet(viewsets.ViewSet):

    @extend_schema(
        parameters=[
            OpenApiParameter(name='bank', description='Funding bank', required=False, type=str)
        ],
        responses={status.HTTP_200_OK: AccountSerializer(many=True)},
        description="List all bank accounts and balances"
    )
    def list(self, request):
        bank = request.query_params.get('bank')

        try:
            accounts = get_accounts(bank)
            serializer = AccountSerializer(accounts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

class DepositViewSet(viewsets.ViewSet):

    @extend_schema(
        parameters=[
            OpenApiParameter(name='start_date', description='Start date for filtering deposits', required=False, type=str, default=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')),
            OpenApiParameter(name='end_date', description='End date for filtering deposits', required=False, type=str, default=datetime.now().strftime('%Y-%m-%d')),
            OpenApiParameter(name='bank', description='Funding bank', required=False, type=str),
            OpenApiParameter(name='account_ids', description='Funding account_id list, comma separated ', required=False, type=str)
        ],
        responses={status.HTTP_200_OK: DepositSerializer(many=True)},
        description="List all pending bank deposits"
    )
    def list(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        bank = request.query_params.get('bank')
        account_ids = request.query_params.get('account_id')
        if account_ids is not None: account_ids = [account_ids]
        
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        try:
            deposits = get_deposits(start_date, end_date, bank, account_ids)
            serializer = DepositSerializer(deposits, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

class RecipientViewSet(viewsets.ViewSet):

    @extend_schema(
        parameters=[
            OpenApiParameter(name='bank', description='Funding bank', required=False, type=str)
        ],
        responses={status.HTTP_200_OK: RecipientSerializer(many=True)},
        description="List all recipients"
    )
    def list(self, request):
        bank = request.query_params.get('bank')
        try:
            recipients = get_recipients(bank)
            serializer = RecipientSerializer(recipients, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)