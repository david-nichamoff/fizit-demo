import logging
import json

from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema
from web3.exceptions import ContractLogicError, BadFunctionCallOutput

from api.serializers.contract_serializer import ContractSerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey

from api.interfaces import ContractAPI, PartyAPI

class ContractViewSet(viewsets.ViewSet):
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.contract_api = ContractAPI()
        self.party_api = PartyAPI()

        self.authenticator = AWSSecretsAPIKeyAuthentication()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

    @extend_schema(
        tags=["Contracts"],
        responses={status.HTTP_200_OK: ContractSerializer(many=True)},
        summary="List Contracts",
        description="Retrieve a list of contracts"
    )
    def list(self, request):
        try:
            contracts = self.contract_api.get_contracts()
            serializer = ContractSerializer(contracts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ContractLogicError as e:
            self.logger.error(f"Contract logic error occurred: {e}")
            return Response({"detail": "Contract logic error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except BadFunctionCallOutput as e:
            self.logger.error(f"Error in contract function call output: {e}")
            return Response({"detail": "Error in contract function call output"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON format in contract data: {e}")
            return Response({"detail": "Invalid JSON format in contract data"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")
            return Response({"detail": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=["Contracts"],
        request=ContractSerializer,
        responses={status.HTTP_201_CREATED: int},
        summary="Create Contract",
        description="Create a new contract"
    )
    def add(self, request):
        auth_info = request.auth
        api_key = auth_info.get("api_key")

        self.logger.info(f"Adding new contract")
        
        if not auth_info.get('is_master_key', False): 
            raise PermissionDenied("You do not have permission to perform this action.")
        
        serializer = ContractSerializer(data=request.data)
        if serializer.is_valid():
            try:
                contract_idx = self.contract_api.add_contract(serializer.validated_data)
                return Response(contract_idx, status=status.HTTP_201_CREATED)
            except Exception as e:
                self.logger.error(f"Error creating contract: {e}")
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        operation_id="retrieve contract",
        tags=["Contracts"],
        responses={status.HTTP_200_OK: ContractSerializer(many=False)},
        summary="Get Contract",
        description="Retrieve a contract"
    )
    def get(self, request, contract_idx=None):
        auth_info = request.auth
        api_key = auth_info.get("api_key")

        try:
            parties = self.party_api.get_parties(contract_idx)
            contract = self.contract_api.get_contract(contract_idx, api_key, parties)
            serializer = ContractSerializer(contract, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            self.logger.error(f"Error retrieving contract {contract_idx}: {e}")
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Contracts"],
        request=ContractSerializer,
        responses={status.HTTP_200_OK: int},
        summary="Update Contract",
        description="Partial update of an existing contract"
    )
    def patch(self, request, contract_idx=None):
        auth_info = request.auth  
        api_key = auth_info.get("api_key")
        
        if not auth_info.get('is_master_key', False): 
            raise PermissionDenied("You do not have permission to perform this action.")

        try:
            parties = self.party_api.get_parties(contract_idx)
            contract_dict = self.contract_api.get_contract(contract_idx, api_key, parties)
            serializer = ContractSerializer(data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            for key, value in serializer.validated_data.items():
                contract_dict[key] = value
            response = self.contract_api.update_contract(contract_idx, contract_dict)
            return Response(response, status=status.HTTP_200_OK)
        except ValidationError as ve:
            self.logger.error(f"Validation error when updating contract {contract_idx}: {ve}")
            return Response(ve.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.logger.error(f"Error updating contract {contract_idx}: {e}")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=["Contracts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Contract",
        description="Delete an existing contract"
    )
    def delete(self, request, contract_idx=None):
        auth_info = request.auth  
        
        if not auth_info.get('is_master_key', False): 
            raise PermissionDenied("You do not have permission to perform this action.")

        try:
            self.contract_api.delete_contract(contract_idx)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as ve:
            self.logger.error(f"Validation error when deleting contract {contract_idx}: {ve}")
            return Response(ve.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.logger.error(f"Error deleting contract {contract_idx}: {e}")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=["Contracts"],
        summary="Get Contract Count",
        description="Retrieve the count of contracts",
        responses={status.HTTP_200_OK: int}
    )
    def get_contract_count(self, request):
        try:
            count = self.contract_api.get_contract_count()
            return Response({"contract_count": count}, status=status.HTTP_200_OK)
        except Exception as e:
            self.logger.error(f"Error retrieving contract count: {e}")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)