import logging

from api.utilities.logging import log_info, log_warning, log_error

class DomainManager:

    CONTRACT_TYPES = ["purchase", "sale", "advance"]
    DEFAULT_CONTRACT_TYPE = "advance"
    DEFAULT_BANK = "manual"
    PARTY_TYPES = ["buyer", "funder", "seller", "client", "affiliate"]
    BANKS = ["token", "mercury", "manual"]

    # These fields are required to make a payment
    BANK_PAYMENT_FIELDS = {
        "mercury": ["account_id", "recipient_id", "amount"],
        "token": ["contract_type", "contract_idx", "funder_addr", "recipient_addr", "token_symbol", "amount", "network"],
        "manual": ["tx_hash", "amount"],
    }

    # These fields are required in the funding JSON fields
    BANK_JSON_FUNDING_FIELDS = {
        "mercury": ["account_id", "recipient_id"],
        "token": ["token_symbol", "network"],
        "manual": []
    }

    # These fields are required in the funding JSON fields
    BANK_JSON_DEPOSIT_FIELDS = {
        "mercury": ["account_id"],
        "token": ["token_symbol", "network"],
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
        "funding_token_network" : "network",
        "deposit_token_symbol": "token_symbol",
        "deposit_token_network": "network",
    }

    BANK_DEPOSIT_FIELDS = {
        "mercury": ["start_date", "end_date", "contract"],
        "token": ["start_date", "end_date", "network", "token_symbol", "parties"]
    }

    CONTRACT_TEMPLATE = {
        "purchase": "admin/add_purchase_contract.html",
        "advance" : "admin/add_advance_contract.html",
        "sale": "admin/add_sale_contract.html"
    }

    CHAIN_REGISTRY = {
        "fizit": {
            "is_poa": True,
            "native_token_symbol": "FIZIT",
            "native_token_decimals": 18
        },
        "avalanche": {
            "is_poa": True,
            "native_token_symbol": "AVAX",
            "native_token_decimals": 18
        }
    }

    CONTRACT_NETWORK = "fizit"

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_contract_types(self):
        return self.CONTRACT_TYPES

    def get_default_contract_type(self):
        return self.DEFAULT_CONTRACT_TYPE

    def get_default_bank(self):
        return self.DEFAULT_BANK

    def get_party_types(self):
        return self.PARTY_TYPES

    def get_banks(self):
        return self.BANKS

    def get_bank_payment_fields(self, bank):
        return self.BANK_PAYMENT_FIELDS.get(bank, [])

    def get_bank_deposit_fields(self, bank):
        return self.BANK_DEPOSIT_FIELDS.get(bank, [])

    def map_payment_fields(self, payment_type):
        return {
            self.BANK_PAYMENT_FIELD_MAPPING.get(field, field): value
            for field, value in payment_type.items()
        }

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
    
    def get_chain_info(self, network):
        """Return metadata for the specified network."""
        return self.CHAIN_REGISTRY.get(network, {})

    def is_poa_chain(self, network):
        """Check if the network uses POA."""
        return self.CHAIN_REGISTRY.get(network, {}).get("is_poa", False)

    def get_native_token_symbol(self, network):
        """Get native token symbol for the network."""
        return self.CHAIN_REGISTRY.get(network, {}).get("native_token_symbol")

    def get_contract_network(self):
        return self.CONTRACT_NETWORK
