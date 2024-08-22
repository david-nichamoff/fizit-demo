import logging

from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.contract_serializer import ContractSerializer

from packages.api_interface import get_contract, get_contracts, add_contract, update_contract, delete_contract

from packages.check_privacy import is_master_key

from api.permissions import HasCustomAPIKey
from api.authentication import CustomAPIKeyAuthentication

class ContractViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Contracts"],
        responses={status.HTTP_200_OK: ContractSerializer(many=True)},
        summary="List Contracts",
        description="Retrieve a list of contracts"
    )
    def list(self, request):
        try:
            contracts = get_contracts(request)
            serializer = ContractSerializer(contracts, many=True)
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
    def add(self, request):
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
        operation_id="retrieve contract",
        tags=["Contracts"],
        responses={status.HTTP_200_OK: ContractSerializer(many=False)},
        summary="Get Contract",
        description="Retrieve a contract"
    )
    def get(self, request, contract_idx=None):
        try:
            contract = get_contract(contract_idx)
            logging.debug("Contract: %s", contract)
            serializer = ContractSerializer(contract, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)
            
    @extend_schema(
        tags=["Contracts"],
        request=ContractSerializer,
        responses={status.HTTP_200_OK: int},
        summary="Update Contract",
        description="Partial update of an existing contract"
    )
    def patch(self, request, contract_idx=None):
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

    @extend_schema(
        tags=["Contracts"],
        request=ContractSerializer,
        responses={status.HTTP_204_NO_CONTENT: int},
        summary="Delete Contract",
        description="Delete an existing contract"
    )
    def delete(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        try:
            response = delete_contract(contract_idx)
            return Response(response, status=status.HTTP_204_NO_CONTENT)
        except ValidationError as ve:
            return Response(ve.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)