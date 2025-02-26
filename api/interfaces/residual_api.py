import datetime
import logging
from decimal import Decimal

from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.web3 import Web3Manager
from api.config import ConfigManager
from api.interfaces import PartyAPI
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning

class BaseResidualAPI(ResponseMixin):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure that the class is a singleton."""
        if not cls._instance:
            cls._instance = super(BaseResidualAPI, cls).__new__(cls)
        return cls._instance

    def __init__(self, registry_manager=None):
        """Initialize ResidualAPI with necessary dependencies."""
        if not hasattr(self, "initialized"):
            self.config_manager = ConfigManager()
            self.w3_manager = Web3Manager()
            self.party_api = PartyAPI()
            self.registry_manager = registry_manager
            self.wallet_addr = self.config_manager.get_wallet_address("Transactor")
            self.logger = logging.getLogger(__name__)
            self.initialized = True

    def get_residuals(self, contract_type, contract_idx):
        """Retrieve residuals for a given contract."""
        try:
            settlement_api = self.registry_manager.get_settlement_api(contract_type)
            response = settlement_api.get_settlements(contract_type, contract_idx)
            if response["status"] == status.HTTP_200_OK:
                settlements = response["data"]
                log_info(self.logger, f"Checking settlements for residuals: {settlements}")

            response = self.party_api.get_parties(contract_type, contract_idx)
            if response["status"] == status.HTTP_200_OK:
                parties = response["data"]
                log_info(self.logger, f"Checking parties for residuals: {parties}")

            contract_api = self.registry_manager.get_contract_api(contract_type)
            response = contract_api.get_contract(contract_type, contract_idx)
            if response["status"] == status.HTTP_200_OK:
                contract = response["data"]
                log_info(self.logger, f"Contract for residuals: {contract}")

            seller_addr, funder_addr = self._get_party_addresses(parties)

            residuals = []
            for settle in settlements:
                if Decimal(settle["residual_calc_amt"]) > Decimal(0.00) and settle["residual_pay_amt"] == "0.00":
                    residual = self._build_residual_dict(contract_type, contract, settle, seller_addr, funder_addr)
                    residuals.append(residual)

            success_message = f"Retrieved {len(residuals)} residuals for {contract_type}:{contract_idx}"
            return self._format_success(residuals, success_message, status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Validation error retrieving residuals for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error retrieving residuals for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_residuals(self, contract_type, contract_idx, residuals):
        """Add residual payments for a contract."""
        try:
            processed_count = 0
            for residual in residuals:
                tx_hash = self._process_residual_payment(residual, contract_type, contract_idx)
                self._post_residual_on_blockchain(residual, contract_type, contract_idx, tx_hash)
                processed_count += 1

            success_message = f"Successfully added {processed_count} residuals for {contract_type}:{contract_idx}"
            return self._format_success({"count" : processed_count}, success_message, status.HTTP_201_CREATED)

        except ValidationError as e:
            error_message = f"Validaton error processing residuals for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error processing residuals for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_party_addresses(self, parties):
        """Retrieve the addresses of the seller and funder."""
        try:
            seller_addr = next((party["party_addr"] for party in parties if party["party_type"] == "seller"), None)
            funder_addr = next((party["party_addr"] for party in parties if party["party_type"] == "funder"), None)
            return seller_addr, funder_addr

        except Exception as e:
            error_message = f"Error retrieving party addresses: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _build_residual_dict(self, contract_type, contract, settle, recipient_addr, funder_addr):
        """Build a residual dictionary for a settlement."""
        try:
            residual_dict = {
                "contract_type": contract_type,
                "contract_idx": contract["contract_idx"],
                "contract_name" : contract["contract_name"],
                "settle_idx": settle["settle_idx"],
                "settle_due_dt": settle["settle_due_dt"],
                "bank": contract["funding_instr"]["bank"],
                "recipient_addr": recipient_addr,
                "funder_addr": funder_addr,
                "residual_calc_amt": settle["residual_calc_amt"],
            }

            optional_fields = ["account_id", "recipient_id", "token_symbol"]
            for field in optional_fields:
                if field in contract["funding_instr"]:
                    residual_dict[field] = contract["funding_instr"][field]

            return residual_dict

        except Exception as e:
            error_message = f"Error building residual dictionary: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _process_residual_payment(self, residual, contract_type, contract_idx):
        """Process the residual payment through the appropriate bank adapter."""
        try:
            adapter = self.registry_manager.get_bank_adapter(residual["bank"])
            required_fields = self.registry_manager.get_bank_payment_fields(residual["bank"])

            mapped_residual = self.registry_manager.map_payment_fields(residual)
            log_info(self.logger, f"Field mapping: {mapped_residual}")

            payment_params = {field: mapped_residual[field] for field in required_fields}
            log_info(self.logger, f"Payment params: {payment_params}")

            tx_hash = adapter.make_payment(**payment_params)
            log_info(self.logger, f"Tx hash: {tx_hash}")

            return tx_hash

        except ValidationError as e:
            error_message = f"Validation error processing payment: {str(e)}"
            log_error(self.logger, error_message)
            raise ValidationError(error_message) from e
        except Exception as e:
            error_message = f"Error processing residual payment: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _post_residual_on_blockchain(self, residual, contract_type, contract_idx, tx_hash):
        """Post the residual payment to the blockchain."""
        try:
            current_time = int(datetime.datetime.now().timestamp())
            payment_amt = int(Decimal(residual["residual_calc_amt"]) * 100)

            w3_contract = self.w3_manager.get_web3_contract(contract_type)
            transaction = w3_contract.functions.payResidual(
                contract_idx, residual["settle_idx"], current_time, payment_amt, tx_hash
            ).build_transaction()

            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_type, contract_idx, "fizit")
            if tx_receipt["status"] != 1:
                raise RuntimeError

        except Exception as e:
            error_message = f"Blockchain transaction_failed"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

### These are for future use

### **Subclass for Advance Contracts**
class PurchaseResidualAPI(BaseResidualAPI):
    pass

### **Subclass for Advance Contracts**
class SaleResidualAPI(BaseResidualAPI):
    pass

### **Subclass for Advance Contracts**
class AdvanceResidualAPI(BaseResidualAPI):
    pass