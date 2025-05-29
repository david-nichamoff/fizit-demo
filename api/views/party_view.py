import logging
from datetime import datetime, timedelta

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import viewsets, status

from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import OpenApiParameter

from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.serializers import PartySerializer, ApprovalSerializer
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

    @extend_schema(
        tags=["Contracts"],
        responses={status.HTTP_200_OK: PartySerializer(many=True)},
        summary="List Contract Parties",
        description="Retrieve a list of parties associated with a contract"
    )
    def list_parties(self, request, contract_type=None, contract_idx=None):
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

    @extend_schema(
        tags=["Contracts"],
        request=PartySerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Create Contract Parties",
        description="Add a list of parties to an existing contract"
    )
    def create_parties(self, request, contract_type=None, contract_idx=None):
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

    @extend_schema(
        tags=["Contracts"],
        request=ApprovalSerializer(many=False),
        responses={status.HTTP_201_CREATED: dict},
        summary="Approve Contract",
        description="Approve a specific contract by setting a party approval"
    )
    def approve_party(self, request, contract_type=None, contract_idx=None, party_idx=None):
        log_info(self.logger, f"Approving party {party_idx} for {contract_type}:{contract_idx}")

        try:
            self._validate_master_key(request.auth)
            self._validate_contract_type(contract_type, self.context.domain_manager)
            contract_api = self.context.api_manager.get_contract_api(contract_type)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            approved_user = request.data.get("approved_user")

            if not approved_user:
                raise ValidationError("Both approved_dt and approved_user are required.")

            party_api = self.context.api_manager.get_party_api()
            response = party_api.approve_party(
                contract_type=contract_type,
                contract_idx=int(contract_idx),
                party_idx=int(party_idx),
                approved_user=approved_user
            )

            if response["status"] != status.HTTP_200_OK:
                log_error(self.logger, f"Approval failed: {response['message']}")
                return Response({"error": response["message"]}, status=response["status"])

            party_response = party_api.get_parties(contract_type, int(contract_idx))
            if party_response["status"] == status.HTTP_200_OK:
                all_approved = all(
                    party.get("approved_dt") and party.get("approved_user")
                    for party in party_response["data"]
                )
                if all_approved:
                    log_info(self.logger, f"All parties approved for {contract_type}:{contract_idx}. Activating contract.")
                    contract_api.set_contract_active(contract_type, int(contract_idx))

            return Response(response["data"], status=status.HTTP_200_OK)

        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @extend_schema(
        tags=["Contracts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Parties",
        description="Delete all parties from a contract",
    )
    def destroy_parties(self, request, contract_type=None, contract_idx=None):
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