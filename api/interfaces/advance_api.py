import datetime
import logging
from decimal import Decimal

from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.config import ConfigManager
from api.web3 import Web3Manager
from api.interfaces import PartyAPI
from api.interfaces.account_api import AccountAPI
from api.interfaces.recipient_api import RecipientAPI
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning
from api.utilities.general import find_match

class BaseAdvanceAPI(ResponseMixin):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure that the class is a singleton."""
        if not cls._instance:
            cls._instance = super(BaseAdvanceAPI, cls).__new__(cls)
        return cls._instance

    def __init__(self, registry_manager=None):
        """Initialize AdvanceAPI with necessary dependencies."""
        if not hasattr(self, "initialized"):
            self.config_manager = ConfigManager()
            self.w3_manager = Web3Manager()
            self.w3 = self.w3_manager.get_web3_instance()

            self.account_api = AccountAPI(registry_manager)
            self.recipient_api = RecipientAPI(registry_manager)
            self.party_api = PartyAPI()

            self.wallet_addr = self.config_manager.get_wallet_address("Transactor")
            self.checksum_wallet_addr = self.w3_manager.get_checksum_address(self.wallet_addr)
            self.registry_manager = registry_manager

            self.logger = logging.getLogger(__name__)
            self.initialized = True

    def get_advances(self, contract_type, contract_idx):

        try:
            transaction_api = self.registry_manager.get_transaction_api(contract_type)
            response = transaction_api.get_transactions(contract_type, contract_idx)
            if response["status"] == status.HTTP_200_OK:
                transactions = response["data"]
                log_info(self.logger, f"Checking transactions for advances: {transactions}")

            response = self.party_api.get_parties(contract_type, contract_idx)
            if response["status"] == status.HTTP_200_OK:
                parties = response["data"]
                log_info(self.logger, f"Checking parties for advances: {parties}")

            contract_api = self.registry_manager.get_contract_api(contract_type)
            response = contract_api.get_contract(contract_type, contract_idx)
            if response["status"] == status.HTTP_200_OK:
                contract = response["data"]
                log_info(self.logger, f"Contract for advances: {contract}")

            advances, accounts, recipients = [], [], []

            response = self._get_accounts(contract["funding_instr"]["bank"])
            if response["status"] == status.HTTP_200_OK:
                accounts = response["data"]

            response = self._get_recipients(contract["funding_instr"]["bank"])
            if response["status"] == status.HTTP_200_OK:
                recipients = response["data"]

            for transact in transactions:
                if transact["advance_pay_amt"] != "0.00" or Decimal(transact["advance_amt"]) <= Decimal(0.00):
                    continue

                party_data = self._extract_party_data(parties)
                advance_dict = self._build_advance_dict(contract_type, contract, transact, party_data, accounts, recipients)
                advances.append(advance_dict)

            success_message =  f"Retrieved advances for {contract_type}:{contract_idx}"
            return self._format_success(advances, success_message, status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Validation error retrieving advances for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Exception retrieving advances for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_advances(self, contract_type, contract_idx, advances):

        try:
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
        """Handle payments based on bank type."""
        try:
            # Get the appropriate adapter
            adapter = self.registry_manager.get_bank_adapter(advance["bank"])

            # Get required fields for the bank
            required_fields = self.registry_manager.get_bank_payment_fields(advance["bank"])
            log_info(self.logger, f"Payment required fields: {required_fields}")

            # Apply field mapping
            mapped_advance = self.registry_manager.map_payment_fields(advance)
            log_info(self.logger, f"Field mapping: {mapped_advance}")

            # Extract parameters dynamically based on required fields
            payment_params = {field: mapped_advance[field] for field in required_fields}
            log_info(self.logger, f"Payment params: {payment_params}")
            
            # Call the adapter's payment method with correctly mapped fields
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

            transaction = self.w3_manager.get_web3_contract(contract_type).functions.payAdvance(
                contract_idx, advance["transact_idx"], current_time, payment_amt, tx_hash
            ).build_transaction()

            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_type, contract_idx, "fizit")

            if tx_receipt["status"] != 1:
                raise RuntimeError("Transaction failed on the blockchain.") from e

        except Exception as e:
            error_message = f"Error recording blockchain transaction: {str(e)}"
            (self.logger, error_message, {"operation": "_record_blockchain_transaction", "contract_idx": contract_idx})
            raise RuntimeError(error_message) from e

    def _get_accounts(self, bank):
        """Retrieve accounts for a given bank."""
        try:
            return self.account_api.get_accounts(bank)
        except Exception as e:
            error_message = f"Error retrieving accounts for bank {bank}: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _get_recipients(self, bank):
        """Retrieve recipients for a given bank."""
        try:
            return self.recipient_api.get_recipients(bank)
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

            return advance_dict
        except Exception as e:
            error_message = f"Error building advance dictionary: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

### These are for future use

### **Subclass for Advance Contracts**
class PurchaseAdvanceAPI(BaseAdvanceAPI):
    pass

### **Subclass for Advance Contracts**
class AdvanceAdvanceAPI(BaseAdvanceAPI):
    pass