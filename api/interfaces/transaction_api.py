import logging
import json
import time

from decimal import Decimal
from datetime import datetime
from json_logic import jsonLogic

from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.managers.app_context import AppContext
from api.interfaces.encryption_api import get_encryptor, get_decryptor
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning
from api.utilities.formatting import from_timestamp

class BaseTransactionAPI(ResponseMixin):

    def __init__(self, context: AppContext):
        """Initialize TransactionAPI with Web3 and configuration settings."""
        self.context = context
        self.config_manager = context.config_manager
        self.domain_manager = context.domain_manager
        self.cache_manager = context.cache_manager
        self.wallet_addr = self.config_manager.get_wallet_address("transactor")
        self.checksum_wallet_addr = self.context.web3_manager.get_checksum_address(self.wallet_addr)
        self.logger = logging.getLogger(__name__)

    def get_transactions(self, contract_type, contract_idx, api_key=None, parties=[], transact_min_dt=None, transact_max_dt=None):
        """Retrieve transactions while ensuring only encrypted values are cached."""
        try:
            cache_key = self.cache_manager.get_transaction_cache_key(contract_type, contract_idx)
            cached_transactions = self.cache_manager.get(cache_key)

            success_message = f"Successfully retrieved transactions for {contract_type}:{contract_idx}"
            decryptor = get_decryptor(api_key, parties)

            contract_api = self.context.api_manager.get_contract_api(contract_type)
            contract = contract_api.get_contract(contract_type, contract_idx, api_key, parties).get("data")

            if cached_transactions is not None:
                log_info(self.logger, f"Loaded transactions for {contract_type}:{contract_idx} from cache")
                parsed_transactions = [
                    self._decrypt_fields(contract_type, contract, idx, raw_transaction, decryptor)
                    for idx, raw_transaction in enumerate(cached_transactions)
                ]
                return self._format_success(parsed_transactions, success_message, status.HTTP_200_OK)

            log_info(self.logger, f"Retrieving transactions for {contract_type}:{contract_idx} from chain")
            network = self.domain_manager.get_contract_network()
            web3_contract = self.context.web3_manager.get_web3_contract(contract_type, network)
            raw_transactions = web3_contract.functions.getTransactions(contract_idx).call()
            log_info(self.logger, f"Retrieve {raw_transactions} from chain")

            self.cache_manager.set(cache_key, raw_transactions, timeout=None)

            parsed_transactions = [
                self._decrypt_fields(contract_type, contract, idx, raw_transaction, decryptor)
                for idx, raw_transaction in enumerate(raw_transactions)
            ]

            return self._format_success(parsed_transactions, success_message, status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Validation error for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error retrieving transactions for {contract_type}:{contract_idx}: {e}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _filter_transaction(self, transaction, transact_min_dt=None, transact_max_dt=None):
        try:
            # Assuming the transaction contains a timestamp at index 1
            transaction_date = datetime.utcfromtimestamp(transaction[1])

            # Normalize `transact_min_dt` and `transact_max_dt` to naive UTC
            if transact_min_dt:
                transact_min_dt = transact_min_dt.replace(tzinfo=None)
            if transact_max_dt:
                transact_max_dt = transact_max_dt.replace(tzinfo=None)

            # Check if the transaction falls within the range
            if transact_min_dt and transaction_date < transact_min_dt:
                return False
            if transact_max_dt and transaction_date >= transact_max_dt:
                return False

            return True

        except Exception as e:
            log_error(self.logger, f"Error filtering transaction: {transaction}, error: {e}")
            return False

    def add_transactions(self, contract_type, contract_idx, transact_logic, transactions):
        """Add transactions to the blockchain for a given contract."""
        try:

            for transaction_dict in transactions:
                log_info(self.logger, f"Sending transaction to chain for {contract_type}:{contract_idx}")
                transact_amt = self._calculate_transaction_amount(transaction_dict, transact_logic)
                log_info(self.logger, f"Calculated transaction amount {transact_amt} with logic {transact_logic}")
                transaction = self._build_transaction(transaction_dict)
                log_info(self.logger, f"Built transaction: {transaction}")

                network = self.domain_manager.get_contract_network()
                web3_contract = self.context.web3_manager.get_web3_contract(contract_type, network)
                
                tx = web3_contract.functions.addTransaction(
                    contract_idx,
                    transaction["extended_data"],
                    transaction["transact_dt"],
                    transact_amt,
                    transaction["transact_data"]
                ).build_transaction()

                self._send_transaction(tx, contract_type, contract_idx, "addTransaction")

            # Sleep to give time for transaction to complete
            time.sleep(self.config_manager.get_network_sleep_time())

            cache_key = self.cache_manager.get_transaction_cache_key(contract_type, contract_idx)
            self.cache_manager.delete(cache_key)
            cache_key = self.cache_manager.get_settlement_cache_key(contract_type, contract_idx)
            self.cache_manager.delete(cache_key)

            success_message = f"Successfully added transactions for {contract_type}:{contract_idx}"
            return self._format_success({"count": len(transactions)}, success_message, status.HTTP_201_CREATED)

        except ValidationError as e:
            error_message = f"Validation error adding transactions for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error adding transactions for {contract_type}:{contract_idx}: {e}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete_transactions(self, contract_type, contract_idx):
        """Delete all transactions for a contract from the blockchain."""
        try:
            network = self.domain_manager.get_contract_network()
            web3_contract = self.context.web3_manager.get_web3_contract(contract_type, network)

            tx = web3_contract.functions.deleteTransactions(contract_idx).build_transaction()
            self._send_transaction(tx, contract_type, contract_idx, "deleteTransactions")

            # Sleep to give time for transaction to complete
            time.sleep(self.config_manager.get_network_sleep_time())

            cache_key = self.cache_manager.get_transaction_cache_key(contract_type, contract_idx)
            self.cache_manager.delete(cache_key)
            cache_key = self.cache_manager.get_settlement_cache_key(contract_type, contract_idx)
            self.cache_manager.delete(cache_key)

            success_message = f"Successfully deleted transactions for {contract_type}:{contract_idx}"
            return self._format_success({ "contract_idx":contract_idx}, success_message, status.HTTP_204_NO_CONTENT)

        except ValidationError as e:
            error_message = f"Validation error for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error deleting transactions for {contract_type}:{contract_idx}: {e}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _calculate_transaction_amount(self, transaction, transact_logic):
        """Calculate the transaction amount using transaction logic."""
        try:
            if "adj" in transaction["transact_data"]:
                return int(Decimal(transaction["transact_data"]["adj"]) * 100)

            return int(jsonLogic(transact_logic, transaction["transact_data"]) * 100)

        except Exception as e:
            error_message = f"Error calculating transaction amount with logic {transact_logic}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _send_transaction(self, tx, contract_type, contract_idx, operation):
        """Send a signed transaction to the blockchain."""
        try:
            tx_receipt = self.context.web3_manager.send_signed_transaction(tx, self.wallet_addr, contract_type, contract_idx, "fizit")

            if tx_receipt["status"] != 1:
                error_message = f"Blockchain {operation} failed for contract {contract_idx}" 
                log_error(self.logger, error_message)
                raise RuntimeError(error_message)

        except Exception as e:
            error_message = f"Error sending transaction: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

### **Subclass for Purchase Contracts**
class PurchaseTransactionAPI(BaseTransactionAPI):

    def _decrypt_fields(self, contract_type, contract, transact_idx, raw_transaction, decryptor):
        """Decrypt fields specific to purchase transactions."""
        try:
            parsed_transaction = self._parse_transaction(contract_type, contract, transact_idx, raw_transaction)
            parsed_transaction["extended_data"] = decryptor.decrypt(raw_transaction[0])
            parsed_transaction["transact_data"] = decryptor.decrypt(raw_transaction[5])
            return parsed_transaction
        except Exception as e:
            raise RuntimeError(f"Decryption failed for purchase transaction {transact_idx}: {e}") from e

    def _parse_transaction(self, contract_type, contract, transact_idx, raw_transaction):
        """Parse a raw transaction from the blockchain into a dictionary."""
        try:
            return {
                "extended_data": raw_transaction[0],
                "transact_dt": from_timestamp(raw_transaction[1]),
                "transact_amt": f"{Decimal(raw_transaction[2]) / 100:.2f}",
                "service_fee_amt": f"{Decimal(raw_transaction[3]) / 100:.2f}",
                "advance_amt": f"{Decimal(raw_transaction[4]) / 100:.2f}",
                "transact_data": raw_transaction[5],
                "advance_pay_dt": from_timestamp(raw_transaction[6]),
                "advance_pay_amt": f"{Decimal(raw_transaction[7]) / 100:.2f}",
                "advance_tx_hash": raw_transaction[8],
                "contract_type": contract_type,
                "contract_idx": contract["contract_idx"],
                "funding_instr": contract["funding_instr"],
                "transact_idx": transact_idx,
            }

        except Exception as e:
            error_message = f"Error parsing transaction {transact_idx}: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _build_transaction(self, transaction_dict):
        """Encrypt fields specific to purchase transactions."""

        encryptor = get_encryptor()
        return {
            "extended_data" : encryptor.encrypt(transaction_dict["extended_data"]),
            "transact_data" : encryptor.encrypt(transaction_dict["transact_data"]),
            "transact_dt" : int(transaction_dict["transact_dt"].timestamp())
        }

### **Subclass for Sale Contracts**
class SaleTransactionAPI(BaseTransactionAPI):
    def _decrypt_fields(self, contract_type, contract, transact_idx, raw_transaction, decryptor):
        """Decrypt fields specific to purchase transactions."""
        try:
            parsed_transaction = self._parse_transaction(contract_type, contract, transact_idx, raw_transaction)
            parsed_transaction["extended_data"] = decryptor.decrypt(raw_transaction[0])
            parsed_transaction["transact_data"] = decryptor.decrypt(raw_transaction[3])
            return parsed_transaction
        except Exception as e:
            raise RuntimeError(f"Decryption failed for purchase transaction {transact_idx}: {e}") from e

    def _parse_transaction(self, contract_type, contract, transact_idx, raw_transaction):
        """Parse a raw transaction from the blockchain into a dictionary."""
        try:
            return {
                "extended_data": raw_transaction[0],
                "transact_dt": from_timestamp(raw_transaction[1]),
                "transact_amt": f"{Decimal(raw_transaction[2]) / 100:.2f}",
                "transact_data": raw_transaction[3],
                "contract_type": contract_type,
                "contract_idx": contract["contract_idx"],
                "funding_instr": contract["funding_instr"],
                "transact_idx": transact_idx,
            }

        except Exception as e:
            error_message = f"Error parsing transaction {transact_idx}: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _build_transaction(self, transaction_dict):
        """Encrypt fields specific to purchase transactions."""

        encryptor = get_encryptor()
        return {
            "extended_data" : encryptor.encrypt(transaction_dict["extended_data"]),
            "transact_data" : encryptor.encrypt(transaction_dict["transact_data"]),
            "transact_dt" : int(transaction_dict["transact_dt"].timestamp())
        }

### **Subclass for Advance Contracts**
class AdvanceTransactionAPI(BaseTransactionAPI):
    def _decrypt_fields(self, contract_type, contract, transact_idx, raw_transaction, decryptor):
        """Decrypt fields specific to purchase transactions."""
        try:
            parsed_transaction = self._parse_transaction(contract_type, contract, transact_idx, raw_transaction)
            parsed_transaction["extended_data"] = decryptor.decrypt(raw_transaction[0])
            parsed_transaction["transact_data"] = decryptor.decrypt(raw_transaction[5])
            return parsed_transaction
        except Exception as e:
            raise RuntimeError(f"Decryption failed for purchase transaction {transact_idx}: {e}") from e

    def _parse_transaction(self, contract_type, contract, transact_idx, raw_transaction):
        """Parse a raw transaction from the blockchain into a dictionary."""
        try:
            return {
                "extended_data": raw_transaction[0],
                "transact_dt": from_timestamp(raw_transaction[1]),
                "transact_amt": f"{Decimal(raw_transaction[2]) / 100:.2f}",
                "service_fee_amt": f"{Decimal(raw_transaction[3]) / 100:.2f}",
                "advance_amt": f"{Decimal(raw_transaction[4]) / 100:.2f}",
                "transact_data": raw_transaction[5],
                "advance_pay_dt": from_timestamp(raw_transaction[6]),
                "advance_pay_amt": f"{Decimal(raw_transaction[7]) / 100:.2f}",
                "advance_tx_hash": raw_transaction[8],
                "contract_type": contract_type,
                "contract_idx": contract["contract_idx"],
                "funding_instr": contract["funding_instr"],
                "transact_idx": transact_idx,
            }

        except Exception as e:
            error_message = f"Error parsing transaction {transact_idx}: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _build_transaction(self, transaction_dict):
        """Encrypt fields specific to purchase transactions."""

        encryptor = get_encryptor()
        return {
            "extended_data" : encryptor.encrypt(transaction_dict["extended_data"]),
            "transact_data" : encryptor.encrypt(transaction_dict["transact_data"]),
            "transact_dt" : int(transaction_dict["transact_dt"].timestamp())
        }
