from datetime import datetime, timedelta

from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .serializers import ContractSerializer, SettlementSerializer, TransactionSerializer, TicketSerializer
from .serializers import ArtifactSerializer, AccountSerializer, RecipientSerializer
from .serializers import PartySerializer
from .serializers import DepositSerializer
from .serializers import DataDictionarySerializer

from packages.interface import get_contract, get_contracts, add_contract, update_contract
from packages.interface import get_contract_parties, add_parties, delete_parties
from packages.interface import get_contract_settlements, get_settlements, add_settlements, delete_settlements
from packages.interface import get_contract_transactions, get_transactions, add_transactions, delete_transactions
from packages.interface import pay_residual, pay_advance, get_deposits
from packages.interface import get_accounts, get_recipients
from packages.interface import get_contract_artifacts, add_artifacts, delete_artifacts
from packages.interface import get_contract_tickets

from packages.privacy import is_master_key

from .models import DataDictionary
from .permissions import HasCustomAPIKey
from .authentication import CustomAPIKeyAuthentication

class ContractViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        operation_id="list_contracts",
        tags=["Contracts"],
        parameters=[
            OpenApiParameter(name='bank', description='Funding bank', required=False, type=str),
            OpenApiParameter(name='account_ids', description='Funding account_id list, comma separated ', required=False, type=str),
        ],
        responses={status.HTTP_200_OK: ContractSerializer(many=True)},
        summary="List Contracts",
        description="Retrieve a list of contracts"
    )
    def list(self, request):
        bank = request.query_params.get('bank')
        account_ids = request.query_params.get('account_ids')
        if account_ids is not None:
            account_ids = account_ids.split(',')
        try:
            contracts = get_contracts(request, bank, account_ids)
            serializer = ContractSerializer(contracts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        operation_id="retrieve contracts",
        tags=["Contracts"],
        responses={status.HTTP_200_OK: ContractSerializer(many=True)},
        summary="Get Contract",
        description="Retrieve a contract"
    )
    def retrieve(self, request, contract_idx=None):
        try:
            contract = get_contract(contract_idx)
            serializer = ContractSerializer(contract, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Contracts"],
        request=ContractSerializer,
        responses={status.HTTP_201_CREATED: int},
        summary="Create Contract",
        description="Create a new contract"
    )
    def create(self, request):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
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
        tags=["Contracts"],
        request=ContractSerializer,
        responses={status.HTTP_200_OK: int},
        summary="Update Contract",
        description="Partial update of an existing contract"
    )
    def partial_update(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        try:
            contract_dict = get_contract(contract_idx)
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

class PartyViewSet(viewsets.ViewSet):
    @extend_schema(
        tags=["Parties"],
        request=PartySerializer(many=True),
        responses={status.HTTP_200_OK: PartySerializer(many=True)},
        summary="List Parties",
        description="Retrieve a list of parties associated with a contract"
    )
    def list_contract(self, request, contract_idx=None):
        try:
            parties = get_contract_parties(int(contract_idx))
            return Response(parties, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Parties"],
        request=PartySerializer(many=True),
        responses={status.HTTP_201_CREATED: int},
        summary="Create Parties",
        description="Add a list of parties to an existing contract",
    )
    def create(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        serializer = PartySerializer(data=request.data, many=True)
        if serializer.is_valid():
            try:
                response = add_parties(contract_idx, serializer.validated_data)
                return Response(response, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)   

    @extend_schema(
        tags=["Parties"],
        responses={status.HTTP_204_NO_CONTENT: int},
        summary="Delete Parties",
        description="Delete all parties from a contract",
    )
    def delete(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        try:
            response = delete_parties(contract_idx)
            return Response(response, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

class SettlementViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Settlement Periods"],
        request=SettlementSerializer(many=True),
        parameters = [
            OpenApiParameter(name='bank', description='Funding bank', required=False, type=str),
            OpenApiParameter(name='account_ids', description='Funding account_id list, comma separated ', required=False, type=str),
        ],
        responses={status.HTTP_200_OK: SettlementSerializer(many=True)},
        summary="List Settlements",
        description="Retrieve a list of settlements"
    )
    def list(self, request):
        bank = request.query_params.get('bank')
        account_ids = request.query_params.get('account_id')
        if account_ids is not None: 
            account_ids = account_ids.split(',')
        try:
            settlements = get_settlements(request, bank, account_ids)
            return Response(settlements, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Settlement Periods"],
        request=SettlementSerializer(many=True),
        responses={status.HTTP_200_OK: SettlementSerializer(many=True)},
        summary="List Settlements",
        description="Retrieve a list of settlements associated with a contract"
    )
    def list_contract(self, request, contract_idx=None):
        try:
            settlements = get_contract_settlements(int(contract_idx))
            return Response(settlements, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Settlement Periods"],
        request=SettlementSerializer(many=True),
        responses={status.HTTP_201_CREATED: int},
        summary="Create Settlements",
        description="Add a list of settlements to an existing contract",
    )
    def create(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
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
        tags=["Settlement Periods"],
        responses={status.HTTP_204_NO_CONTENT: int},
        summary="Delete Settlements",
        description="Delete all settlements from a contract",
    )
    def delete(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        try:
            response = delete_settlements(contract_idx)
            return Response(response, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

class TransactionViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Transactions"],
        parameters = [
            OpenApiParameter(name='bank', description='Funding bank', required=False, type=str),
            OpenApiParameter(name='account_ids', description='Funding account_id list, comma separated ', required=False, type=str),
        ],
        responses={status.HTTP_200_OK: TransactionSerializer(many=True)},
        summary="List Transactions",
        description="Retrieve a list of transactions"
    )
    def list(self, request):
        bank = request.query_params.get('bank')
        account_ids = request.query_params.get('account_ids')
        if account_ids is not None: 
            account_ids = account_ids.split(',')
        try:
            transactions = get_transactions(request, bank, account_ids)
            return Response(transactions, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Transactions"],
        responses={status.HTTP_200_OK: TransactionSerializer(many=True)},
        summary="List Transactions",
        description="Retrieve a list of transactions associated with a contract"
    )
    def list_contract(self, request, contract_idx=None):
        try:
            transactions = get_contract_transactions(int(contract_idx))
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
    def create(self, request, contract_idx=None):
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
    def delete(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        try:
            response = delete_transactions(contract_idx)
            return Response(response, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

class TicketViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Tickets"],
        parameters=[
            OpenApiParameter(name='start_date', description='Start date for filtering tickets', required=True, type=str, default=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')),
            OpenApiParameter(name='end_date', description='End date for filtering tickets', required=True, type=str, default=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')), 
        ],
        responses={status.HTTP_200_OK: TicketSerializer(many=True)},
        summary="List Tickets from Host",
        description="Retrieve a list of all tickets associated with a contract from host"
    )
    def list_contract(self, request, contract_idx=None):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            tickets = get_contract_tickets(contract_idx, start_date, end_date)
            return Response(tickets, status=status.HTTP_200_OK)
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


class ArtifactViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Artifacts"],
        responses={status.HTTP_200_OK: ArtifactSerializer(many=True)},
        summary="List Artifacts",
        description="Retrieve a list of artifacts associated with a contract"
    )
    def list_contract(self, request, contract_idx=None):
        try:
            artifacts = get_contract_artifacts(int(contract_idx))
            return Response(artifacts, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Artifacts"],
        responses={status.HTTP_201_CREATED: str},
        summary="Create Artifacts",
        description="Search file system for artifacts for a contract",
    )
    def create(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        try:
            contract_name = get_contract(contract_idx)["contract_name"]
            response = add_artifacts(contract_idx, contract_name)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Artifacts"],
        responses={status.HTTP_204_NO_CONTENT: int},
        summary="Delete Artifacts",
        description="Delete all artifacts from a contract",
    )
    def delete(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        try:
            response = delete_artifacts(contract_idx)
            return Response(response, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

class AccountViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Float Accounts"],
        parameters=[
            OpenApiParameter(name='bank', description='Funding bank', required=False, type=str),
        ],
        responses={status.HTTP_200_OK: AccountSerializer(many=True)},
        summary="List Acounts",
        description="Retrieve a list of all bank accounts and balances"
    )
    def list(self, request):
        bank = request.query_params.get('bank')
        try:
            accounts = get_accounts(bank)
            return Response(accounts, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Float Accounts"],
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
        tags=["Float Accounts"],
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

    @extend_schema(
        tags=["Float Accounts"],
        responses={status.HTTP_200_OK: str},
        description="Initiate advance payment"
    )
    @action(detail=True, methods=['post'], url_path='pay-advance')
    def pay_advance(self, request, account_id=None):
        try:
            response = pay_advance(account_id)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DepositViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Float Accounts"],
        parameters=[
            OpenApiParameter(name='start_date', description='Start date for filtering deposits', required=True, type=str, default=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')),
            OpenApiParameter(name='end_date', description='End date for filtering deposits', required=True, type=str, default=datetime.now().strftime('%Y-%m-%d')),
        ],
        responses={status.HTTP_200_OK: DepositSerializer(many=True)},
        summary="List Deposits",
        description="Retrieve a list of all pending bank deposits"
    )
    def list(self, request, account_id=None):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            deposits = get_deposits(start_date, end_date, account_id)
            serializer = DepositSerializer(deposits, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

class RecipientViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Float Accounts"],
        parameters=[
            OpenApiParameter(name='bank', description='Funding bank', required=False, type=str)
        ],
        responses={status.HTTP_200_OK: RecipientSerializer(many=True)},
        summary="List Recipients",
        description="Retrieve a list of all recipients"
    )
    def list(self, request):
        bank = request.query_params.get('bank')
        try:
            recipients = get_recipients(bank)
            serializer = RecipientSerializer(recipients, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

class DataDictionaryViewSet(viewsets.ViewSet):

    @extend_schema(
        tags=["Data Dictionary"],
        summary="Retrieve Data Dictionary",
        description="Retrieve the data dictionary"
    )
    def list(self, request):
        language_code = request.query_params.get('language_code', 'en')
        queryset = DataDictionary.objects.filter(language_code=language_code)
        serializer = DataDictionarySerializer(queryset, many=True)
        return Response(serializer.data)

