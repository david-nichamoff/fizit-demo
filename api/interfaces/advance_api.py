import datetime
import logging
from decimal import Decimal

from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.managers import ConfigManager, Web3Manager
from api.interfaces import TransactionAPI, ContractAPI, PartyAPI
from api.adapters.bank import MercuryAdapter, TokenAdapter
from api.interfaces.account_api import AccountAPI
from api.interfaces.recipient_api import RecipientAPI

from api.mixins import ValidationMixin, AdapterMixin, InterfaceResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning
from api.utilities.general import find_match

class AdvanceAPI(ValidationMixin, AdapterMixin, InterfaceResponseMixin):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure that the class is a singleton."""
        if not cls._instance:
            cls._instance = super(AdvanceAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize AdvanceAPI with necessary dependencies."""
        if not hasattr(self, "initialized"):
            self.config_manager = ConfigManager()
            self.config = self.config_manager.load_config()
            self.w3_manager = Web3Manager()
            self.w3 = self.w3_manager.get_web3_instance()

            self.transaction_api = TransactionAPI()
            self.contract_api = ContractAPI()
            self.account_api = AccountAPI()
            self.recipient_api = RecipientAPI()
            self.party_api = PartyAPI()

            self.wallet_addr = self.config_manager.get_nested_config_value("wallet_addr", "Transactor")
            self.checksum_wallet_addr = self.w3_manager.get_checksum_address(self.wallet_addr)

            self.mercury_adapter = MercuryAdapter()
            self.token_adapter = TokenAdapter()

            self.logger = logging.getLogger(__name__)
            self.initialized = True

    def get_advances(self, contract_idx):
        """Retrieve advances for a contract."""

        try:
            # Validate contract_idx
            self._validate_contract_idx(contract_idx, self.contract_api)

            advances = []

            response = self.transaction_api.get_transactions(contract_idx)
            if response["status"] == status.HTTP_200_OK:
                transactions = response["data"]
                log_info(self.logger, f"Checking transactions for advances: {transactions}")

            response = self.party_api.get_parties(contract_idx)
            if response["status"] == status.HTTP_200_OK:
                parties = response["data"]
                log_info(self.logger, f"Checking parties for advances: {parties}")

            response = self.contract_api.get_contract(contract_idx)
            if response["status"] == status.HTTP_200_OK:
                contract = response["data"]
                log_info(self.logger, f"Contract for advances: {contract}")

            accounts, recipients = [], []
            if contract["funding_instr"]["bank"] == "mercury":
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
                advance_dict = self._build_advance_dict(contract, transact, party_data, accounts, recipients)
                advances.append(advance_dict)

            success_message =  f"Retrieved advances for contract {contract_idx}"
            return self._format_success(advances, success_message, status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Validation error retrieving advances for contract '{contract_idx}': {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Exception retrieving advances for contract '{contract_idx}': {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_advances(self, contract_idx, advances):
        """Process advance payments."""
        try:
            # Validate contract_idx
            self._validate_contract_idx(contract_idx, self.contract_api)

            processed_count = 0
            for advance in advances:
                self._make_payment(advance)
                self._record_blockchain_transaction(contract_idx, advance)
                processed_count += 1

            success_message =  f"Added advances for contract {contract_idx}"
            return self._format_success({"count" : processed_count}, success_message, status.HTTP_201_CREATED)

        except ValidationError as e:
            error_message = f"Validation error adding advances for contract '{contract_idx}': {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Exception adding advances for contract '{contract_idx}': {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _make_payment(self, advance):
        """Handle payments based on bank type."""
        try:
            # Get the appropriate adapter
            adapter = self._get_bank_adapter(advance["bank"])
            
            # Dynamically call the `make_payment` method based on bank type
            if advance["bank"] == "mercury":
                adapter.make_payment(
                    advance["account_id"], advance["recipient_id"], advance["advance_amt"]
                )
            elif advance["bank"] == "token":
                adapter.make_payment(
                    advance["contract_idx"], advance["funder_addr"], advance["recipient_addr"],
                    advance["token_symbol"], advance["advance_amt"]
                )

        except ValidationError as e:
            error_message = f"Validation error processing payment: {str(e)}"
            log_error(self.logger, error_message)
            raise ValidationError(error_message) from e
        except Exception as e:
            error_message = f"Error processing payment: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _record_blockchain_transaction(self, contract_idx, advance):
        """Record advance payment on the blockchain."""
        try:
            current_time = int(datetime.datetime.now().timestamp())
            payment_amt = int(Decimal(advance["advance_amt"]) * 100)

            transaction = self.w3_manager.get_web3_contract().functions.payAdvance(
                contract_idx, advance["transact_idx"], current_time, payment_amt
            ).build_transaction()

            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")

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

    def _build_advance_dict(self, contract, transact, party_data, accounts, recipients):
        """Build the advance dictionary."""
        try:
            log_info(self.logger, f"Building advance dictionary for contract: {contract}")

            funding_instr = contract["funding_instr"]
            log_info(self.logger,f"Checking validity of funding instructions: {funding_instr}")
            # Check if funding_instr is a dictionary
            if isinstance(funding_instr, dict):
                log_info(self.logger, f"Contract funding instructions are valid: {funding_instr}")
            else:
                log_error(self.logger, f"Contract funding instructions are NOT a valid dictionary: {funding_instr}")

            advance_dict = {
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