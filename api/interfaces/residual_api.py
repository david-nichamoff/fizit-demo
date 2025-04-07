import datetime
import logging
from decimal import Decimal

from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.managers.app_context import AppContext
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning

class BaseResidualAPI(ResponseMixin):

    def __init__(self, context: AppContext):
        self.context = context
        self.config_manager = context.config_manager
        self.cache_manager = context.cache_manager
        self.domain_manager = context.domain_manager
        self.wallet_addr = self.config_manager.get_wallet_address("Transactor")
        self.logger = logging.getLogger(__name__)

    def get_residuals(self, contract, parties, settlements):
        """Retrieve residuals for a given contract."""
        try:
            seller_addr, funder_addr = self._get_party_addresses(parties)

            residuals = []
            for settlement in settlements:
                if Decimal(settlement["residual_calc_amt"]) > Decimal(0.00) and settlement["residual_pay_amt"] == "0.00":
                    residual = self._build_residual_dict(contract["contract_type"], contract, settlement, seller_addr, funder_addr)
                    residuals.append(residual)

            success_message = f"Retrieved {len(residuals)} residuals for {contract["contract_type"]}:{contract["contract_idx"]}"
            return self._format_success(residuals, success_message, status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Validation error retrieving residuals for {contract["contract_type"]}:{contract["contract_idx"]}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error retrieving residuals for {contract["contract_type"]}:{contract["contract_idx"]}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_residuals(self, contract_type, contract_idx, residuals):
        """Add residual payments for a contract."""
        try:
            cache_key = self.cache_manager.get_transaction_cache_key(contract_type, contract_idx)
            self.cache_manager.delete(cache_key)
            cache_key = self.cache_manager.get_settlement_cache_key(contract_type, contract_idx)
            self.cache_manager.delete(cache_key)

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

            optional_fields = ["account_id", "recipient_id", "token_symbol", "network"]
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
            adapter = self.context.adapter_manager.get_bank_adapter(residual["bank"])

            required_fields = self.domain_manager.get_bank_payment_fields(residual["bank"])
            mapped_residual = self.domain_manager.map_payment_fields(residual)
            payment_params = {field: mapped_residual[field] for field in required_fields}

            tx_hash = adapter.make_payment(**payment_params)

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

            network = self.domain_manager.get_contract_network()
            web3_contract = self.context.web3_manager.get_web3_contract(contract_type, network)
            transaction = web3_contract.functions.payResidual(
                contract_idx, residual["settle_idx"], current_time, payment_amt, tx_hash
            ).build_transaction()

            network = self.domain_manager.get_contract_network()
            tx_receipt = self.context.web3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_type, contract_idx, network)

            if tx_receipt["status"] != 1:
                raise RuntimeError

        except Exception as e:
            error_message = f"Blockchain transaction_failed"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e


### **Subclass for Advance Contracts**
class AdvanceResidualAPI(BaseResidualAPI):
    pass