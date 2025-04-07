import logging

from api.serializers import (
    PurchaseContractSerializer, SaleContractSerializer, AdvanceContractSerializer,
    SaleSettlementSerializer, AdvanceSettlementSerializer,
    PurchaseTransactionSerializer, SaleTransactionSerializer, AdvanceTransactionSerializer,
)

from api.utilities.logging import log_info, log_warning, log_error

class SerializerManager:

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)

        self.contract_serializers = {
            "purchase": PurchaseContractSerializer,
            "sale": SaleContractSerializer,
            "advance": AdvanceContractSerializer
        }

        self.settlement_serializers = {
            "purchase": None,
            "sale": SaleSettlementSerializer,
            "advance": AdvanceSettlementSerializer
        }

        self.transaction_serializers = {
            "purchase": PurchaseTransactionSerializer,
            "sale": SaleTransactionSerializer,
            "advance": AdvanceTransactionSerializer
        }

    # Initialize Serializers
    def get_contract_serializer(self, contract_type):
        return self.contract_serializers.get(contract_type, None)

    def get_settlement_serializer(self, contract_type):
        return self.settlement_serializers.get(contract_type, None)

    def get_transaction_serializer(self, contract_type):
        return self.transaction_serializers.get(contract_type, None)