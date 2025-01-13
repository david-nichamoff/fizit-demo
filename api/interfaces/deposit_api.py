import logging
from decimal import Decimal

from api.adapters.bank import MercuryAdapter, TokenAdapter
from api.managers import Web3Manager, ConfigManager
from api.interfaces import ContractAPI, TransactionAPI

from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.mixins import ValidationMixin, AdapterMixin, InterfaceResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning

class DepositAPI(ValidationMixin, InterfaceResponseMixin, AdapterMixin):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure the class is a singleton."""
        if not cls._instance:
            cls._instance = super(DepositAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize the class with config, Web3, and logger."""
        if not hasattr(self, "initialized"):
            self.config_manager = ConfigManager()
            self.config = self.config_manager.load_config()
            self.w3_manager = Web3Manager()
            self.w3 = self.w3_manager.get_web3_instance()
            self.w3_contract = self.w3_manager.get_web3_contract()
            self.transaction_api = TransactionAPI()
            self.contract_api = ContractAPI()

            self.mercury_adapter = MercuryAdapter()
            self.token_adapter = TokenAdapter()

            self.logger = logging.getLogger(__name__)
            self.initialized = True

            self.wallet_addr = self.config_manager.get_nested_config_value("wallet_addr", "Transactor")

    def get_deposits(self, start_date, end_date, contract_idx):
        """Retrieve deposits for a contract."""
        try:
            self._validate_contract_idx(contract_idx, self.contract_api)

            response = self.contract_api.get_contract(contract_idx)
            if response["status"] == status.HTTP_200_OK:
                contract = response["data"]
            else:
                raise RuntimeError("Cannot retrieve contract")

            bank = contract.get("deposit_instr", {}).get("bank")

            log_info(self.logger, f"Validate bank {bank} for contract {contract_idx}")
            self._validate_bank_type(bank, contract_idx)

            # Get the appropriate adapter
            adapter = self._get_bank_adapter(bank)

            if bank == "mercury":
                deposits = adapter.get_deposits(start_date, end_date, contract)
            elif bank == "token":
                token_symbol = contract["funding_instr"].get("token_symbol", "unknown")
                deposits = adapter.get_deposits(start_date, end_date, token_symbol, contract)

            return self._format_success(deposits, f"Retried deposits for contract {contract_idx}", status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Data error retrieving deposits for contract {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Unexpected error retrieving deposits for contract {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_deposit(self, contract_idx, deposit):
        """Post deposit to the blockchain."""
        log_info(self.logger, f"Deposit to post: {deposit}")

        try:
            self._validate_contract_idx(contract_idx, self.contract_api)
            self._process_deposit(contract_idx, deposit)

            success_message = f"Added deposit"
            return self._format_success({"count": 1},success_message,status.HTTP_201_CREATED)

        except ValidationError as e:
            error_message = f"Data error adding deposits for contract {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error adding deposits for contract {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _validate_bank_type(self, bank_type, contract_idx):
        """Validate if the bank type is supported."""
        if bank_type not in ["mercury", "token"]:
            error_message = f"Unsupported bank type '{bank_type}' for contract {contract_idx}"
            log_error(self.logger, error_message)
            raise ValidationError(error_message)

    def _process_deposit(self, contract_idx, deposit):
        """Process a single deposit."""
        try:
            payment_amt = int(Decimal(deposit["deposit_amt"]) * 100)
            settlement_timestamp = self._convert_to_midnight_timestamp(deposit["deposit_dt"])
            settle_idx = deposit["settle_idx"]
            dispute_reason = deposit.get("dispute_reason", "")

            transaction = self._build_transaction(contract_idx, settle_idx, settlement_timestamp, payment_amt, dispute_reason)
            self._send_transaction(transaction, contract_idx)

        except Exception as e:
            error_message = f"Error processing deposit {deposit.get('deposit_id')} for contract {contract_idx}: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _convert_to_midnight_timestamp(self, deposit_dt):
        """Convert a datetime to a timestamp at midnight UTC."""
        try:
            settlement_date = deposit_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            return int(settlement_date.timestamp())
        except Exception as e:
            error_message = f"Invalid date format for deposit date: {deposit_dt}"
            log_error(self.logger, error_message)
            raise ValidationError(error_message) from e

    def _build_transaction(self, contract_idx, settle_idx, settlement_timestamp, payment_amt, dispute_reason):
        """Build the blockchain transaction for a deposit."""
        try:
            return self.w3_contract.functions.postSettlement(
                contract_idx, settle_idx, settlement_timestamp, payment_amt, dispute_reason
            ).build_transaction()
        except Exception as e:
            error_message = f"Error building transaction for contract {contract_idx}: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _send_transaction(self, transaction, contract_idx):
        """Send a signed transaction to the blockchain."""
        try:
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")

            if tx_receipt["status"] != 1:
                raise RuntimeError(f"Transaction failed with status: {tx_receipt['status']}")

        except Exception as e:
            error_message = f"Error sending transaction for contract {contract_idx}: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e