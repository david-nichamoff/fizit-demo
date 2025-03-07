import logging
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import viewsets, status

from drf_spectacular.utils import extend_schema

from api.serializers.distribution_serializer import DistributionSerializer
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.registry import RegistryManager
from api.views.mixins.validation import ValidationMixin
from api.views.mixins.permission import PermissionMixin
from api.utilities.logging import log_error, log_info, log_warning


class DistributionViewSet(viewsets.ViewSet, ValidationMixin, PermissionMixin):
    """
    A ViewSet for managing distributions associated with different contract types.
    """
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.registry_manager = RegistryManager()
        self.logger = logging.getLogger(__name__)

### **Sale Contract Distributions**

    @extend_schema(
        tags=["Sale Contracts"],
        responses={status.HTTP_200_OK: DistributionSerializer(many=True)},
        summary="List Sale Contract Distributions",
        description="Retrieve a list of distributions associated with a sale contract."
    )
    def list_sale_distributions(self, request, contract_idx=None):
        return self._list_distributions(request, "sale", contract_idx)

    @extend_schema(
        tags=["Sale Contracts"],
        request=DistributionSerializer(many=True),
        responses={status.HTTP_201_CREATED: dict},
        summary="Create Sale Contract Distributions",
        description="Initiate distribution payments for a sale contract."
    )
    def create_sale_distributions(self, request, contract_idx=None):
        return self._create_distributions(request, "sale", contract_idx)

### **Core Functions**

    def _list_distributions(self, request, contract_type, contract_idx):
        log_info(self.logger, f"Fetching distributions for {contract_type}:{contract_idx}.")

        try:
            self._validate_contract_type(contract_type, self.registry_manager)
            contract_api = self.registry_manager.get_contract_api(contract_type)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            distribution_api = self.registry_manager.get_distribution_api(contract_type)
            response = distribution_api.get_distributions(contract_type, int(contract_idx))

            if response["status"] == status.HTTP_200_OK:
                serializer = DistributionSerializer(response["data"], many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": response["message"]}, status=response["status"])

        except ValidationError as e:
            log_error(self.logger, f"Validation error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_distributions(self, request, contract_type, contract_idx):
        log_info(self.logger, f"Initiating distribution payment for {contract_type}:{contract_idx}.")

        try:
            self._validate_master_key(request.auth)
            self._validate_contract_type(contract_type, self.registry_manager)
            contract_api = self.registry_manager.get_contract_api(contract_type)
            self._validate_contract_idx(contract_idx, contract_type, contract_api)

            serializer = DistributionSerializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)

            distribution_api = self.registry_manager.get_distribution_api(contract_type)
            response = distribution_api.add_distributions(contract_type, int(contract_idx), serializer.validated_data)

            if response["status"] == status.HTTP_201_CREATED:
                log_info(self.logger, f"Successfully initiated distribution payments for {contract_type}:{contract_idx}")
                return Response(response["data"], status=status.HTTP_201_CREATED)
            else:
                return Response({"error": response["message"]}, status=response["status"])

        except PermissionDenied as pd:
            log_error(self.logger, f"Permission denied for {contract_type}:{contract_idx}: {pd}")
            return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            log_error(self.logger, f"Validation error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)