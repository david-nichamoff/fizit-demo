import datetime
import logging
from decimal import Decimal

from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.managers.app_context import AppContext
from api.interfaces.mixins import ResponseMixin
from api.utilities.general import find_match
from api.utilities.logging import  log_error, log_info, log_warning

class BaseAdvanceAPI(ResponseMixin):

    def __init__(self, context: AppContext):
        self.context = context
        self.config_manager = context.config_manager
        self.cache_manager = context.cache_manager
        self.domain_manager = context.domain_manager

        # Other common items
        self.wallet_addr = self.config_manager.get_wallet_address("transactor")
        self.checksum_wallet_addr = self.context.web3_manager.get_checksum_address(self.wallet_addr)

        self.logger = logging.getLogger(__name__)

    def get_advances(self, contract, transactions, parties, accounts, recipients):
        try:
            advances = []
            for transaction in transactions:
                if transaction["advance_pay_amt"] != "0.00" or Decimal(transaction["advance_amt"]) <= Decimal(0.00):
                    continue

                party_data = self._extract_party_data(parties)
                advance_dict = self._build_advance_dict(contract["contract_type"], contract, transaction, party_data, accounts, recipients)
                advances.append(advance_dict)

            success_message =  f"Retrieved advances for {contract["contract_type"]}:{contract["contract_idx"]}"
            return self._format_success(advances, success_message, status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Validation error retrieving advances for {contract["contract_type"]}:{contract["contract_idx"]}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Exception retrieving advances for {contract["contract_type"]}:{contract["contract_idx"]}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_advances(self, contract_type, contract_idx, advances):
        try:
            self.cache_manager.delete(self.cache_manager.get_transaction_cache_key(contract_type, contract_idx))
            self.cache_manager.delete(self.cache_manager.get_settlement_cache_key(contract_type, contract_idx))

            processed_count = 0
            for advance in advances:
                tx_hash = self._make_payment(advance)
                self._record_blockchain_transaction(contract_type, contract_idx, advance, tx_hash)
                processed_count += 1

            success_message =  f"Added advances for {contract_type}:{contract_idx}"
            return self._format_success({"count" : processed_count}, success_message, status.HTTP_201_CREATED)

        except ValidationError as e:
            error_message = f"Validation error adding advances for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Exception adding advances for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _make_payment(self, advance):
        try:
            adapter = self.context.adapter_manager.get_bank_adapter(advance["bank"])
            required_fields = self.domain_manager.get_bank_payment_fields(advance["bank"])
            log_info(self.logger, f"Payment required fields: {required_fields}")

            mapped_advance = self.domain_manager.map_payment_fields(advance)
            payment_params = {field: mapped_advance[field] for field in required_fields}
            
            tx_hash =  adapter.make_payment(**payment_params)
            log_info(self.logger, f"Tx hash: {tx_hash}")
            
            return tx_hash

        except ValidationError as e:
            error_message = f"Validation error processing payment: {str(e)}"
            log_error(self.logger, error_message)
            raise ValidationError(error_message) from e
        except Exception as e:
            error_message = f"Error processing payment: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _record_blockchain_transaction(self, contract_type, contract_idx, advance, tx_hash):
        try:
            current_time = int(datetime.datetime.now().timestamp())
            payment_amt = int(Decimal(advance["advance_amt"]) * 100)

            network = self.domain_manager.get_contract_network()
            transaction = self.context.web3_manager.get_web3_contract(contract_type, network).functions.payAdvance(
                contract_idx, advance["transact_idx"], current_time, payment_amt, tx_hash
            ).build_transaction()

            tx_receipt = self.context.web3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_type, contract_idx, network)

            if tx_receipt["status"] != 1:
                raise RuntimeError("Transaction failed on the blockchain.") from e

        except Exception as e:
            error_message = f"Error recording blockchain transaction: {str(e)}"
            (self.logger, error_message, {"operation": "_record_blockchain_transaction", "contract_idx": contract_idx})
            raise RuntimeError(error_message) from e

    def _get_accounts(self, bank):
        """Retrieve accounts for a given bank."""
        try:
            return self.context.api_manager.get_account_api().get_accounts(bank)
        except Exception as e:
            error_message = f"Error retrieving accounts for bank {bank}: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _get_recipients(self, bank):
        """Retrieve recipients for a given bank."""
        try:
            return self.contect.api_manager.get_recipient_api().get_recipients(bank)
        except Exception as e:
            error_message = f"Error retrieving recipients for bank {bank}: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _extract_party_data(self, parties):
        """Extract party data for seller and funder."""
        try:
            party_data = {}
            for party in parties:
                if party.get("party_type") == "seller":
                    party_data["recipient_addr"] = party.get("party_addr")
                    party_data["recipient_party_code"] = party["party_code"]
                elif party.get("party_type") == "funder":
                    party_data["funder_addr"] = party.get("party_addr")
                    party_data["funder_party_code"] = party["party_code"]
            return party_data
        except Exception as e:
            error_message = f"Error extracting party data: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _build_advance_dict(self, contract_type, contract, transact, party_data, accounts, recipients):
        """Build the advance dictionary."""
        try:
            log_info(self.logger, f"Building advance dictionary for contract: {contract}")
            funding_instr = contract["funding_instr"]

            advance_dict = {
                "contract_type": contract_type,
                "contract_idx": contract["contract_idx"],
                "contract_name": contract["contract_name"],
                "transact_idx": transact["transact_idx"],
                "transact_dt": transact["transact_dt"],
                "bank": contract["funding_instr"]["bank"],
                **party_data,
                "advance_amt": transact["advance_amt"]
            }

            log_info(self.logger, f"Advance dictionary: {advance_dict}")

            if contract["funding_instr"].get("account_id"):
                advance_dict["account_id"] = contract["funding_instr"]["account_id"]
                advance_dict["account_name"] = find_match(
                    accounts, "account_id", contract["funding_instr"]["account_id"], "account_name", "N/A"
                )

            if contract["funding_instr"].get("recipient_id"):
                advance_dict["recipient_id"] = contract["funding_instr"]["recipient_id"]
                advance_dict["recipient_name"] = find_match(
                    recipients, "recipient_id", contract["funding_instr"]["recipient_id"], "recipient_name", "N/A"
                )

            if contract["funding_instr"].get("token_symbol"):
                advance_dict["token_symbol"] = contract["funding_instr"]["token_symbol"]

            if contract["funding_instr"].get("network"):
                advance_dict["network"] = contract["funding_instr"]["network"]

            return advance_dict
        except Exception as e:
            error_message = f"Error building advance dictionary: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

### **Subclass for Advance Contracts**
class PurchaseAdvanceAPI(BaseAdvanceAPI):
    pass

### **Subclass for Advance Contracts**
class AdvanceAdvanceAPI(BaseAdvanceAPI):
    pass