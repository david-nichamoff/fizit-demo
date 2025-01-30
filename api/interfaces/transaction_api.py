import logging
import json

from decimal import Decimal
from datetime import datetime
from json_logic import jsonLogic

from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.web3 import Web3Manager
from api.config import ConfigManager
from api.registry import RegistryManager
from api.interfaces.encryption_api import get_encryptor, get_decryptor
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning
from api.utilities.formatting import from_timestamp

class TransactionAPI(ResponseMixin):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure the class is a singleton."""
        if not cls._instance:
            cls._instance = super(TransactionAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize TransactionAPI with Web3 and configuration settings."""
        if not hasattr(self, "initialized"):
            self.config_manager = ConfigManager()
            self.registry_manager = RegistryManager()
            self.w3_manager = Web3Manager()
            self.w3 = self.w3_manager.get_web3_instance()
            self.wallet_addr = self.config_manager.get_wallet_address("Transactor")
            self.checksum_wallet_addr = self.w3_manager.get_checksum_address(self.wallet_addr)

            self.logger = logging.getLogger(__name__)
            self.initialized = True

    def get_transactions(self, contract_type, contract_idx, api_key=None, parties=[], transact_min_dt=None, transact_max_dt=None):
        """Retrieve transactions for a contract within a date range."""
        try:
            contract_api = self.registry_manager.get_contract_api(contract_type)
            contract = contract_api.get_contract(contract_type, contract_idx, api_key, parties).get("data")
            log_info(self.logger, f"Retrieving contracts for {contract_type}:{contract_idx} with data {contract}")

            w3_contract = self.w3_manager.get_web3_contract(contract_type) 
            raw_transactions = w3_contract.functions.getTransactions(contract_idx).call()
            log_info(self.logger, f"Retrieved raw transaction data {raw_transactions}")

            transactions = [
                self._parse_transaction(t, idx, contract_type, contract, api_key, parties)
                for idx, t in enumerate(raw_transactions)
                if self._filter_transaction(t, transact_min_dt, transact_max_dt)
            ]

            success_message = f"Successfully retrieved transactions for {contract_type}:{contract_idx}"
            data = sorted(transactions, key=lambda t: t["transact_dt"], reverse=True)
            return self._format_success(data, success_message, status.HTTP_200_OK)

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

    def add_transactions(self, contract_type, contract_idx, transact_logic, transactions, api_key):
        """Add transactions to the blockchain for a given contract."""
        try:
            encryptor = get_encryptor()

            for transaction in transactions:
                encrypted_data = self._encrypt_transaction_data(transaction, encryptor)
                transact_amt = self._calculate_transaction_amount(transaction, transact_logic)

                w3_contract = self.w3_manager.get_web3_contract(contract_type)
                tx = w3_contract.functions.addTransaction(
                    contract_idx,
                    encrypted_data["extended_data"],
                    int(transaction["transact_dt"].timestamp()),
                    transact_amt,
                    encrypted_data["transact_data"]
                ).build_transaction()

                self._send_transaction(tx, contract_type, contract_idx, "addTransaction")

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
            w3_contract = self.w3_manager.get_web3_contract(contract_type)
            tx = w3_contract.functions.deleteTransactions(contract_idx).build_transaction()
            self._send_transaction(tx, contract_type, contract_idx, "deleteTransactions")

            success_message = f"Successfully deleted transactions for {contract_type}:{contract_idx}"
            return self._format_success({ "contract_idx":contract_idx}, success_message, status.HTTP_204_NO_CONTENT)

        except ValidationError as e:
            error_message = f"Validation error for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error deleting transactions for {contract_type}:{contract_idx}: {e}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _parse_transaction(self, transact, idx, contract_type, contract, api_key, parties):
        """Parse a raw transaction from the blockchain into a dictionary."""
        decryptor = get_decryptor(api_key, parties)
        try:
            return {
                "extended_data": decryptor.decrypt(transact[0]),
                "transact_dt": from_timestamp(transact[1]),
                "transact_amt": f"{Decimal(transact[2]) / 100:.2f}",
                "service_fee_amt": f"{Decimal(transact[3]) / 100:.2f}",
                "advance_amt": f"{Decimal(transact[4]) / 100:.2f}",
                "transact_data": decryptor.decrypt(transact[5]),
                "advance_pay_dt": from_timestamp(transact[6]),
                "advance_pay_amt": f"{Decimal(transact[7]) / 100:.2f}",
                "advance_tx_hash": transact[8],
                "contract_type": contract_type,
                "contract_idx": contract["contract_idx"],
                "funding_instr": contract["funding_instr"],
                "transact_idx": idx,
            }

        except Exception as e:
            error_message = f"Error parsing transaction {idx}: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e


    def _encrypt_transaction_data(self, transaction, encryptor):
        """Encrypt sensitive transaction data."""

        try:
            return {
                "extended_data": encryptor.encrypt(transaction["extended_data"]),
                "transact_data": encryptor.encrypt(transaction["transact_data"]),
            }
        except Exception as e:
            error_message = "Error decryting data"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

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
            tx_receipt = self.w3_manager.send_signed_transaction(tx, self.wallet_addr, contract_type, contract_idx, "fizit")

            if tx_receipt["status"] != 1:
                error_message = f"Blockchain {operation} failed for contract {contract_idx}" 
                log_error(self.logger, error_message)
                raise RuntimeError(error_message) from e

        except Exception as e:
            error_message = f"Error sending transaction: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e