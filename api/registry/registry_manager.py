from api.interfaces import AdvanceContractAPI, TicketingContractAPI
from api.serializers import AdvanceContractSerializer, TicketingContractSerializer
from api.adapters.bank import MercuryAdapter, TokenAdapter

class RegistryManager:
    """Registry for static contract APIs, serializers, and fixed business logic."""

    _instance = None

    CONTRACT_TYPES = [
        "advance",
        "ticketing"
    ]

    CONTRACT_APIS = {
        "advance": AdvanceContractAPI(),
        "ticketing": TicketingContractAPI(),
    }

    CONTRACT_SERIALIZERS = {
        "advance": AdvanceContractSerializer,
        "ticketing": TicketingContractSerializer,
    }

    PARTY_TYPES = [
        "buyer",
        "funder",
        "seller",
        "affiliate",
    ]

    BANK_TYPES = [
        "token",
        "mercury",
    ]

    BANK_ADAPTERS = {
        "mercury": MercuryAdapter(),
        "token": TokenAdapter(),
    }

    BANK_PAYMENT_FIELDS = {
        "mercury": ["account_id", "recipient_id", "amount"],
        "token": ["contract_type", "contract_idx", "funder_addr", "recipient_addr", "token_symbol", "amount"],
    }

    BANK_PAYMENT_FIELD_MAPPING = {
        "advance_amt": "amount",  # Map advance_amt -> amount
        "residual_calc_amt": "amount",  # Map residual_amt -> amount
    }

    BANK_DEPOSIT_FIELDS = {
        "mercury": ["start_date", "end_date", "contract"],
        "token": ["start_date", "end_date", "token_symbol", "contract_type", "contract"]
    }

    def __new__(cls):
        """Ensure Singleton instance for RegistryManager."""
        if not cls._instance:
            cls._instance = super(RegistryManager, cls).__new__(cls)
        return cls._instance

    def get_contract_types(self):
        """Retrieve all allowed contract types."""
        return self.CONTRACT_TYPES

    def get_contract_api(self, contract_type):
        """Retrieve the API handler for a contract type."""
        return self.CONTRACT_APIS.get(contract_type, None)

    def get_contract_serializer(self, contract_type):
        """Retrieve the serializer for a contract type."""
        return self.CONTRACT_SERIALIZERS.get(contract_type, None)

    def get_party_types(self):
        """Retrieve all allowed party types."""
        return self.PARTY_TYPES

    def get_bank_types(self):
        """Retrieve all allowed bank types."""
        return self.BANK_TYPES

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
    