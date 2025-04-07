import logging

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import viewsets, status

from drf_spectacular.utils import extend_schema

from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.serializers import PartySerializer
from api.views.mixins import ValidationMixin, PermissionMixin
from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_error, log_info, log_warning

class PartyViewSet(viewsets.ViewSet, ValidationMixin, PermissionMixin):
    """
    A ViewSet for managing parties associated with a contract.
    """
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = build_app_context()
        self.logger = logging.getLogger(__name__)

### **Purchase Contracts**

    @extend_schema(
        tags=["Purchase Contracts"],
        responses={status.HTTP_200_OK: PartySerializer(many=True)},
        summary="List Purchase Contract Parties",
        description="Retrieve a list of parties associated with a purchase contract"
    )
    def list_purchase_parties(self, request, contract_idx=None):
        return self._list_parties(request, contract_type="purchase", contract_idx=contract_idx)

    @extend_schema(
        tags=["Purchase Contracts"],
        request=PartySerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Create Purchase Contract Parties",
        description="Add a list of parties to an existing purchase contract"
    )
    def create_purchase_parties(self, request, contract_idx=None):
        return self._create_parties(request, contract_type="purchase", contract_idx=contract_idx)

    @extend_schema(
        tags=["Purchase Contracts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Purchase Contract Parties",
        description="Delete all parties from a contract",
    )
    def destroy_purchase_parties(self, request, contract_idx=None):
        return self._destroy_parties(request, contract_type="purchase", contract_idx=contract_idx)

### **Sale Contracts**

    @extend_schema(
        tags=["Sale Contracts"],
        responses={status.HTTP_200_OK: PartySerializer(many=True)},
        summary="List Sale Contract Parties",
        description="Retrieve a list of parties associated with a sale contract"
    )
    def list_sale_parties(self, request, contract_idx=None):
        return self._list_parties(request, contract_type="sale", contract_idx=contract_idx)

    @extend_schema(
        tags=["Sale Contracts"],
        request=PartySerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Create Sale Contract Parties",
        description="Add a list of parties to an existing sale contract"
    )
    def create_sale_parties(self, request, contract_idx=None):
        return self._create_parties(request, contract_type="sale", contract_idx=contract_idx)

    @extend_schema(
        tags=["Sale Contracts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Sale Contract Parties",
        description="Delete all parties from a contract",
    )
    def destroy_sale_parties(self, request, contract_idx=None):
        return self._destroy_parties(request, contract_type="sale", contract_idx=contract_idx)

### **Advance Contracts**

    @extend_schema(
        tags=["Advance Contracts"],
        responses={status.HTTP_200_OK: PartySerializer(many=True)},
        summary="List Advance Contract Parties",
        description="Retrieve a list of parties associated with a advance contract"
    )
    def list_advance_parties(self, request, contract_idx=None):
        return self._list_parties(request, contract_type="advance", contract_idx=contract_idx)

    @extend_schema(
        tags=["Advance Contracts"],
        request=PartySerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Create Advance Contract Parties",
        description="Add a list of parties to an existing advance contract"
    )
    def create_advance_parties(self, request, contract_idx=None):
        return self._create_parties(request, contract_type="advance", contract_idx=contract_idx)

    @extend_schema(
        tags=["Advance Contracts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Advance Contract Parties",
        description="Delete all parties from a contract",
    )
    def destroy_advance_parties(self, request, contract_idx=None):
        return self._destroy_parties(request, contract_type="advance", contract_idx=contract_idx)

### **Core Functions**

    def _list_parties(self, request, contract_type=None, contract_idx=None):
        log_info(self.logger, f"Fetching parties for {contract_type}:{contract_idx}")

        try:
            contract_api = self.context.api_manager.get_contract_api(contract_type)
            self._validate_contract_type(contract_type, self.context.domain_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            party_api = self.context.api_manager.get_party_api()
            response = party_api.get_parties(contract_type, int(contract_idx))
            if response["status"] == status.HTTP_200_OK:
                serializer = PartySerializer(response["data"], many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_parties(self, request, contract_type=None, contract_idx=None):
        log_info(self.logger, f"Attempting to add parties to {contract_type}:{contract_idx}")

        try:
            self._validate_master_key(request.auth)
            self._validate_contract_type(contract_type, self.context.domain_manager)

            contract_api = self.context.api_manager.get_contract_api(contract_type)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            validated_data = self._validate_request_data(PartySerializer, request.data, many=True)
            self._validate_parties(validated_data, self.context.config_manager)

            party_api = self.context.api_manager.get_party_api()
            response = party_api.add_parties(contract_type, int(contract_idx), validated_data)
            log_info(self.logger, f"Successfully added parties to {contract_type}:{contract_idx}")

            if response["status"] == status.HTTP_201_CREATED:
                return Response(response["data"], status=status.HTTP_201_CREATED)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except PermissionDenied as pd:
            log_error(self.logger, f"Permission denied for {contract_type}:{contract_idx}: {pd}")
            return Response({"detail": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _destroy_parties(self, request, contract_type=None, contract_idx=None):
        log_info(self.logger, f"Attempting to delete all parties for {contract_type}:{contract_idx}")

        try:
            contract_api = self.context.api_manager.get_contract_api(contract_type)
            self._validate_master_key(request.auth)
            self._validate_contract_type(contract_type, self.context.domain_manager)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            party_api = self.context.api_manager.get_party_api()
            response = party_api.delete_parties(contract_type, int(contract_idx))

            if response["status"] == status.HTTP_204_NO_CONTENT:
                return Response(response["data"], status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error" : response["message"]}, response["status"])

        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)