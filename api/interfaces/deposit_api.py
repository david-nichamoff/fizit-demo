import logging
from decimal import Decimal

from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.web3 import Web3Manager
from api.config import ConfigManager
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning

class BaseDepositAPI(ResponseMixin):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure the class is a singleton."""
        if not cls._instance:
            cls._instance = super(BaseDepositAPI, cls).__new__(cls)
        return cls._instance

    def __init__(self, registry_manager=None):
        """Initialize the class with config, Web3, and logger."""
        if not hasattr(self, "initialized"):
            self.logger = logging.getLogger(__name__)
            self.config_manager = ConfigManager()
            self.w3_manager = Web3Manager()
            self.w3 = self.w3_manager.get_web3_instance()
            self.registry_manager = registry_manager
            self.wallet_addr = self.config_manager.get_wallet_address("Transactor")
            self.initialized = True

    def get_deposits(self, start_date, end_date, contract_type, contract_idx):
        """Retrieve deposits for a contract."""
        try:
            contract_api = self.registry_manager.get_contract_api(contract_type)
            response = contract_api.get_contract(contract_type, contract_idx)
            contract = response.get("data", {})
            log_info(self.logger, f"Contract to retrieve deposits: {contract}")

            bank = contract.get("deposit_instr", {}).get("bank")
            log_info(self.logger, f"Bank: {bank}")

            log_info(self.logger, f"Validate bank {bank} for {contract_type}:{contract_idx}")

            # Get the appropriate adapter
            adapter = self.registry_manager.get_bank_adapter(bank)
            required_fields = self.registry_manager.get_bank_deposit_fields(bank)

            payment_params = {"start_date": start_date, "end_date": end_date, "contract": contract}

            if "token_symbol" in required_fields:
                token_symbol = contract["funding_instr"].get("token_symbol", "unknown")
                payment_params.update({"token_symbol" : token_symbol})

            if "contract_type" in required_fields:
                payment_params.update({"contract_type" : contract_type})
            
            # Call the make_payment method dynamically
            deposits = adapter.get_deposits(**payment_params)
            return self._format_success(deposits, f"Retried deposits for contract {contract_idx}", status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Data error retrieving deposits for contract {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Unexpected error retrieving deposits for contract {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_deposit(self, contract_type, contract_idx, deposit):
        """Post deposit to the blockchain."""
        log_info(self.logger, f"Deposit to post: {deposit}")

        try:
            self._process_deposit(contract_type, contract_idx, deposit)
            return self._format_success({"count": 1},"Added deposit",status.HTTP_201_CREATED)

        except ValidationError as e:
            error_message = f"Data error adding deposits for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error adding deposits for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)


    def _convert_to_midnight_timestamp(self, deposit_dt):
        """Convert a datetime to a timestamp at midnight UTC."""
        try:
            settlement_date = deposit_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            return int(settlement_date.timestamp())
        except Exception as e:
            error_message = f"Invalid date format for deposit date: {deposit_dt}"
            log_error(self.logger, error_message)
            raise ValidationError(error_message) from e



    def _send_transaction(self, transaction, contract_type, contract_idx):
        """Send a signed transaction to the blockchain."""
        try:
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_type, contract_idx, "fizit")

            if tx_receipt["status"] != 1:
                raise RuntimeError(f"Transaction failed with status: {tx_receipt['status']}")

        except Exception as e:
            error_message = f"Error sending transaction for {contract_type}:{contract_idx}: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

### **Subclass for Advance Contracts**
class AdvanceDepositAPI(BaseDepositAPI):
    def _process_deposit(self, contract_type, contract_idx, deposit):
        """Process a single deposit."""
        try:
            payment_amt = int(Decimal(deposit["deposit_amt"]) * 100)
            settlement_timestamp = self._convert_to_midnight_timestamp(deposit["deposit_dt"])
            settle_idx = deposit["settle_idx"]
            dispute_reason = deposit.get("dispute_reason", "")
            tx_hash = deposit.get("tx_hash", "")

            transaction = self._build_transaction(contract_type, contract_idx, settle_idx, settlement_timestamp, payment_amt, tx_hash, dispute_reason)
            self._send_transaction(transaction, contract_type, contract_idx)

        except Exception as e:
            error_message = f"Error processing deposit {deposit.get('tx_hash')} for {contract_type}:{contract_idx}: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _build_transaction(self, contract_type, contract_idx, settle_idx, settlement_timestamp, payment_amt, tx_hash, dispute_reason):

        try:
            w3_contract = self.w3_manager.get_web3_contract(contract_type)
            return w3_contract.functions.postSettlement(
                contract_idx, settle_idx, settlement_timestamp, payment_amt, tx_hash, dispute_reason
            ).build_transaction()
        except Exception as e:
            error_message = f"Error building transaction for {contract_type}:{contract_idx}: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e


### **Subclass for Sale Contracts**
class SaleDepositAPI(BaseDepositAPI):
    def _process_deposit(self, contract_type, contract_idx, deposit):
        """Process a single deposit."""
        try:
            payment_amt = int(Decimal(deposit["deposit_amt"]) * 100)
            settlement_timestamp = self._convert_to_midnight_timestamp(deposit["deposit_dt"])
            settle_idx = deposit["settle_idx"]
            dispute_reason = deposit.get("dispute_reason", "")
            tx_hash = deposit.get("tx_hash", "")

            transaction = self._build_transaction(contract_type, contract_idx, settle_idx, settlement_timestamp, payment_amt, tx_hash)
            self._send_transaction(transaction, contract_type, contract_idx)

        except Exception as e:
            error_message = f"Error processing deposit {deposit.get('tx_hash')} for {contract_type}:{contract_idx}: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _build_transaction(self, contract_type, contract_idx, settle_idx, settlement_timestamp, payment_amt, tx_hash):

        try:
            w3_contract = self.w3_manager.get_web3_contract(contract_type)
            return w3_contract.functions.postSettlement(
                contract_idx, settle_idx, settlement_timestamp, payment_amt, tx_hash
            ).build_transaction()
        except Exception as e:
            error_message = f"Error building transaction for {contract_type}:{contract_idx}: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e
