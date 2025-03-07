import logging

from api.interfaces import PurchaseContractAPI, SaleContractAPI, AdvanceContractAPI
from api.interfaces import SaleSettlementAPI, AdvanceSettlementAPI
from api.interfaces import PurchaseTransactionAPI, SaleTransactionAPI, AdvanceTransactionAPI
from api.interfaces import SaleDepositAPI, AdvanceDepositAPI
from api.interfaces import PurchaseAdvanceAPI, AdvanceAdvanceAPI
from api.interfaces import PurchaseResidualAPI, SaleResidualAPI, AdvanceResidualAPI
from api.interfaces import SaleDistributionAPI
from api.serializers import PurchaseContractSerializer, SaleContractSerializer, AdvanceContractSerializer
from api.serializers import SaleSettlementSerializer, AdvanceSettlementSerializer
from api.serializers import PurchaseTransactionSerializer, SaleTransactionSerializer, AdvanceTransactionSerializer
from api.adapters.bank import MercuryAdapter, TokenAdapter, ManualAdapter
from api.utilities.logging import log_info, log_warning, log_error

class RegistryManager:
    """Registry for static contract APIs, serializers, and fixed business logic."""

    _instance = None

    CONTRACT_TYPES = [
        "purchase",
        "sale",
        "advance"
    ]

    DEFAULT_CONTRACT_TYPE = "advance"
    DEFAULT_BANK = "manual"

    CONTRACT_SERIALIZERS = {
        "purchase": PurchaseContractSerializer,
        "sale": SaleContractSerializer,
        "advance": AdvanceContractSerializer
    }

    SETTLEMENT_SERIALIZERS = {
        "purchase": None,
        "sale": SaleSettlementSerializer,
        "advance": AdvanceSettlementSerializer
    }

    TRANSACTION_SERIALIZERS = {
        "purchase": PurchaseTransactionSerializer,
        "sale": SaleTransactionSerializer,
        "advance": AdvanceTransactionSerializer
    }

    PARTY_TYPES = [
        "buyer",
        "funder",
        "seller",
        "client",
        "affiliate"
    ]

    BANKS = [
        "token",
        "mercury",
        "manual"
    ]

    BANK_ADAPTERS = {
        "mercury": MercuryAdapter(),
        "token": TokenAdapter(),
        "manual": ManualAdapter()
    }

    # These fields are required to make a payment
    BANK_PAYMENT_FIELDS = {
        "mercury": ["account_id", "recipient_id", "amount"],
        "token": ["contract_type", "contract_idx", "funder_addr", "recipient_addr", "token_symbol", "amount"],
        "manual": ["tx_hash", "amount"],
    }

    # These fields are required in the funding JSON fields
    BANK_JSON_FUNDING_FIELDS = {
        "mercury": ["account_id", "recipient_id"],
        "token": ["token_symbol"],
        "manual": []
    }

    # These fields are required in the funding JSON fields
    BANK_JSON_DEPOSIT_FIELDS = {
        "mercury": ["account_id"],
        "token": ["token_symbol"],
        "manual": []
    }

    BANK_PAYMENT_FIELD_MAPPING = {
        "advance_amt": "amount",  
        "residual_calc_amt": "amount",  
        "distribution_calc_amt": "amount",
    
        # Bank-specific mappings for json
        "funding_account": "account_id",
        "funding_recipient": "recipient_id",
        "deposit_account": "account_id",
        "funding_token_symbol": "token_symbol",
        "deposit_token_symbol": "token_symbol",
    }

    BANK_DEPOSIT_FIELDS = {
        "mercury": ["start_date", "end_date", "contract"],
        "token": ["start_date", "end_date", "token_symbol", "contract_type", "contract"]
    }

    CONTRACT_TEMPLATE = {
        "purchase": "admin/add_purchase_contract.html",
        "advance" : "admin/add_advance_contract.html",
        "sale": "admin/add_sale_contract.html"
    }

    def __new__(cls):
        """Ensure Singleton instance for RegistryManager."""
        if not cls._instance:
            cls._instance = super(RegistryManager, cls).__new__(cls)
            cls._instance._initialize_apis()
        return cls._instance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def _initialize_apis(self):
        """Initialize APIs with registry manager for dependency injection."""
        self.CONTRACT_APIS = {
            "purchase": PurchaseContractAPI(self),
            "sale": SaleContractAPI(self),
            "advance": AdvanceContractAPI(self),
        }

        self.SETTLEMENT_APIS = {
            "purchase": None,
            "sale": SaleSettlementAPI(self),
            "advance": AdvanceSettlementAPI(self),
        }

        self.TRANSACTION_APIS = {
            "purchase": PurchaseTransactionAPI(self),
            "sale": SaleTransactionAPI(self),
            "advance": AdvanceTransactionAPI(self),
        }

        self.DEPOSIT_APIS = {
            "purchase": None,
            "sale": SaleDepositAPI(self),
            "advance": AdvanceDepositAPI(self),
        }

        self.ADVANCE_APIS = {
            "purchase": PurchaseAdvanceAPI(self),
            "sale": None,
            "advance": AdvanceAdvanceAPI(self),
        }

        self.DISTRIBUTION_APIS = {
            "purchase": None,
            "sale": SaleDistributionAPI(self),
            "advance": None
        }

        self.RESIDUAL_APIS = {
            "purchase": None,
            "sale": None,
            "advance": AdvanceResidualAPI(self),
        }

    def get_contract_types(self):
        """Retrieve all allowed contract types."""
        return self.CONTRACT_TYPES

    def get_default_contract_type(self):
        return self.DEFAULT_CONTRACT_TYPE

    def get_default_bank(self):
        return self.DEFAULT_BANK

    def get_contract_api(self, contract_type):
        """Retrieve the API handler for a contract type."""
        return self.CONTRACT_APIS.get(contract_type)

    def get_contract_serializer(self, contract_type):
        """Retrieve the serializer for a contract type."""
        return self.CONTRACT_SERIALIZERS.get(contract_type, None)

    def get_settlement_api(self, contract_type):
        """Retrieve the API handler for a contract type."""
        return self.SETTLEMENT_APIS.get(contract_type)

    def get_deposit_api(self, contract_type):
        """Retrieve the API handler for a contract type."""
        return self.DEPOSIT_APIS.get(contract_type)

    def get_advance_api(self, contract_type):
        """Retrieve the API handler for a contract type."""
        return self.ADVANCE_APIS.get(contract_type)

    def get_distribution_api(self, contract_type):
        """Retrieve the API handler for a contract type."""
        return self.DISTRIBUTION_APIS.get(contract_type)

    def get_residual_api(self, contract_type):
        """Retrieve the API handler for a contract type."""
        return self.RESIDUAL_APIS.get(contract_type)

    def get_settlement_serializer(self, contract_type):
        """Retrieve the serializer for a contract type."""
        return self.SETTLEMENT_SERIALIZERS.get(contract_type, None)

    def get_transaction_api(self, contract_type):
        """Retrieve the API handler for a contract type."""
        return self.TRANSACTION_APIS.get(contract_type)

    def get_transaction_serializer(self, contract_type):
        """Retrieve the serializer for a contract type."""
        return self.TRANSACTION_SERIALIZERS.get(contract_type, None)

    def get_party_types(self):
        """Retrieve all allowed party types."""
        return self.PARTY_TYPES

    def get_banks(self):
        """Retrieve all allowed banks."""
        return self.BANKS

    def get_bank_adapter(self, bank):
        """Retrieve the adapter for the specified bank."""
        return self.BANK_ADAPTERS.get(bank, None)

    def get_bank_payment_fields(self, bank):
        """Retrieve the required fields for a bank's make_payment method."""
        return self.BANK_PAYMENT_FIELDS.get(bank, [])

    def get_bank_deposit_fields(self, bank):
        """Retrieve the required fields for a bank's get_deposits method."""
        return self.BANK_DEPOSIT_FIELDS.get(bank, [])

    def map_payment_fields(self, payment_type):
        """Map the field names to match adapter expected parameters."""
        return {
            self.BANK_PAYMENT_FIELD_MAPPING.get(field, field): value
            for field, value in payment_type.items()
        }

    def get_contract_form(self, contract_type):
        """Lazy import to avoid circular dependency"""
        from frontend.forms import PurchaseContractForm, AdvanceContractForm, SaleContractForm

        contract_forms = {
            "purchase": PurchaseContractForm,
            "advance": AdvanceContractForm,
            "sale": SaleContractForm
        }
        return contract_forms.get(contract_type)

    def get_settlement_form(self, contract_type):
        """Lazy import to avoid circular dependency"""
        from frontend.forms import SaleSettlementForm, AdvanceSettlementForm

        settlement_forms = {
            "advance": AdvanceSettlementForm,
            "sale": SaleSettlementForm,
            "purchase": None
        }
        return settlement_forms.get(contract_type)
    
    def get_contract_template(self, contract_type):
        return self.CONTRACT_TEMPLATE.get(contract_type)

    def generate_instruction_data(self, transaction_type, bank, **kwargs):
        if bank not in self.BANKS:
            log_error(self.logger, f"Invalid bank '{bank}' passed to generate_instruction_data")
            return {}

        log_info(self.logger, f"Generating instruction data for {transaction_type} on {bank} with kwargs: {kwargs}")

        instruction_data = {"bank": bank}

        # Determine required fields based on transaction type
        required_fields = (
            self.BANK_JSON_FUNDING_FIELDS.get(bank, [])
            if transaction_type == "funding"
            else self.BANK_JSON_DEPOSIT_FIELDS.get(bank, [])
        )

        log_info(self.logger, f"Required fields for {transaction_type} on {bank}: {required_fields}")

        # Apply field mapping so `kwargs` keys match expected values
        transformed_kwargs = {
            self.BANK_PAYMENT_FIELD_MAPPING.get(k, k): v for k, v in kwargs.items()
        }

        log_info(self.logger, f"Transformed kwargs after applying field mapping: {transformed_kwargs}")

        for field in required_fields:
            if field in transformed_kwargs:
                instruction_data[field] = transformed_kwargs[field]
            else:
                log_error(self.logger, f"Missing expected field '{field}' for {transaction_type} on {bank}")

        log_info(self.logger, f"Final instruction data for {transaction_type} on {bank}: {instruction_data}")

        return instruction_data