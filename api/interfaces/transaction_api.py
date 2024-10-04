import datetime
import logging
import json

from datetime import timezone, datetime, time
from decimal import Decimal
from json_logic import jsonLogic

from api.managers import Web3Manager, ConfigManager
from api.interfaces import ContractAPI

from api.interfaces.encryption_api import get_encryptor, get_decryptor
from .util_api import is_valid_json

class TransactionAPI:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure that the class is a singleton."""
        if not cls._instance:
            cls._instance = super(TransactionAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize TransactionsAPI with Web3 and configuration settings."""
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.w3_manager = Web3Manager()
        self.w3 = self.w3_manager.get_web3_instance()
        self.w3_contract = self.w3_manager.get_web3_contract()
        self.contract_api = ContractAPI()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

    def from_timestamp(self, ts):
        return None if ts == 0 else datetime.fromtimestamp(ts, tz=timezone.utc)

    def get_transact_dict(self, transact, transact_idx, contract, api_key, parties):
        decryptor = get_decryptor(api_key, parties)

        try:
             # Initialize encryption API 
            decrypted_extended_data = decryptor.decrypt(transact[0])
            decrypted_transact_data = decryptor.decrypt(transact[5])

            transact_dict = {
                "extended_data": decrypted_extended_data,
                "transact_dt": self.from_timestamp(transact[1]),
                "transact_amt": f'{Decimal(transact[2]) / 100:.2f}',
                "service_fee_amt": f'{Decimal(transact[3]) / 100:.2f}',
                "advance_amt": f'{Decimal(transact[4]) / 100:.2f}',
                "transact_data": decrypted_transact_data,
                "advance_pay_dt": self.from_timestamp(transact[6]),
                "advance_pay_amt": f'{Decimal(transact[7]) / 100:.2f}',
                "advance_confirm": transact[8],
                "contract_idx": contract['contract_idx'],
                "funding_instr": contract['funding_instr'],
                "transact_idx": transact_idx
            }

            self.logger.debug("Transaction amount (String): %s", transact_dict["transact_amt"])
            self.logger.debug("Transaction amount type: %s", type(transact_dict["transact_amt"]))

            return transact_dict
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            self.logger.error(f"Error creating transaction dictionary: {str(e)}")
            raise ValueError(f"Invalid transaction data: {str(e)}")

    def get_transactions(self, contract_idx, api_key=None, parties=[], transact_min_dt=None, transact_max_dt=None):
        try:
            transactions = []
            contract = self.contract_api.get_contract(contract_idx, api_key, parties)

            transacts = self.w3_contract.functions.getTransactions(contract['contract_idx']).call()
            for transact in transacts:
                transact_dict = self.get_transact_dict(transact, len(transactions), contract, api_key, parties)
                transact_dt = transact_dict['transact_dt']

                if transact_min_dt and transact_dt < transact_min_dt:
                    continue  # Skip transactions before the minimum date
                if transact_max_dt and transact_dt >= transact_max_dt:
                    continue  # Skip transactions after the maximum date

                transactions.append(transact_dict)

            sorted_transactions = sorted(transactions, key=lambda d: d['transact_dt'], reverse=True)
            return sorted_transactions
        except Exception as e:
            self.logger.error(f"Error retrieving transactions for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to retrieve transactions for contract {contract_idx}") from e

    def add_transactions(self, contract_idx, transact_logic, transactions, api_key):
        self.validate_transactions(transactions)

        encryptor = get_encryptor()

        try:
            for transaction in transactions:
                # Encrypt sensitive fields before sending to the blockchain
                encrypted_extended_data = encryptor.encrypt(transaction["extended_data"])
                encrypted_transact_data = encryptor.encrypt(transaction["transact_data"])

                transact_dt = int(transaction["transact_dt"].timestamp())
                transact_data = transaction["transact_data"]

                # Check if 'adj' is in transact_data for adjustment
                if "adj" in transaction["transact_data"]:
                    transact_amt = int(Decimal(transaction["transact_data"]["adj"]) * 100)
                else:
                    transact_amt = int(jsonLogic(transact_logic, transact_data) * 100)

                nonce = self.w3.eth.get_transaction_count(self.config["wallet_addr"])

                # Build the transaction
                call_function = self.w3_contract.functions.addTransaction(
                    contract_idx, encrypted_extended_data, transact_dt, transact_amt, encrypted_transact_data
                ).build_transaction(
                    {"from": self.config["wallet_addr"], "nonce": nonce, "gas": self.config["gas_limit"]}
                )
                tx_receipt = self.w3_manager.get_tx_receipt(call_function)
                if tx_receipt["status"] != 1:
                    raise RuntimeError(f"Failed to add transaction for contract {contract_idx}. Transaction status: {tx_receipt['status']}")

            return True
        except Exception as e:
            self.logger.error(f"Error adding transactions for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to add transactions for contract {contract_idx}") from e

    def delete_transactions(self, contract_idx):
        try:
            nonce = self.w3.eth.get_transaction_count(self.config["wallet_addr"])
            self.logger.info(f"Initiating delete for contract {contract_idx} from {self.config['wallet_addr']}")
            
            # Estimate the gas required for the transaction
            transaction = self.w3_contract.functions.deleteTransactions(contract_idx).build_transaction({
                "from": self.config["wallet_addr"],
                "nonce": nonce
            })

            estimated_gas = self.w3.eth.estimate_gas(transaction)
            self.logger.info(f"Estimated gas for deleteTransactions: {estimated_gas}")
            gas_limit = max(estimated_gas, self.config["gas_limit"]) 
            self.logger.info(f"Final gas limit: {gas_limit}")

            # Build the transaction with the estimated gas limit
            transaction["gas"] = gas_limit
            tx_receipt = self.w3_manager.get_tx_receipt(transaction)
            
            if tx_receipt["status"] != 1:
                raise RuntimeError(f"Failed to delete transactions for contract {contract_idx}. Transaction status: {tx_receipt['status']}")
            
            return True

        except Exception as e:
            self.logger.error(f"Error deleting transactions for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to delete transactions for contract {contract_idx}") from e

    def validate_transactions(self, transactions):
        try:
            for transaction in transactions:
                # Validate extended_data as valid JSON
                if not is_valid_json(transaction.get("extended_data", "")):
                    raise ValueError(f"Invalid JSON for 'extended_data': {transaction['extended_data']}")

                # Validate transact_data as valid JSON
                if not is_valid_json(transaction.get("transact_data", "")):
                    raise ValueError(f"Invalid JSON for 'transact_data': {transaction['transact_data']}")
        except ValueError as e:
            self.logger.error(f"Transaction validation error: {str(e)}")
            raise

    def import_transactions(self, contract_idx, transactions):
        """
        Import historical transactions to a given contract using the Solidity importTransaction function.
        
        :param contract_idx: The index of the contract to which the transactions will be imported.
        :param transactions: List of transaction dictionaries to be imported.
        """
        try:
            encryptor = get_encryptor()

            for transaction in transactions:
                # Convert datetime fields from string to datetime object, then to Unix timestamps
                transact_dt = int(datetime.fromisoformat(transaction["transact_dt"]).timestamp())
                advance_pay_dt = int(datetime.fromisoformat(transaction["advance_pay_dt"]).timestamp()) if transaction["advance_pay_dt"] else 0

                # Encrypt sensitive fields before sending to the blockchain
                encrypted_extended_data = encryptor.encrypt(transaction["extended_data"])
                encrypted_transact_data = encryptor.encrypt(transaction["transact_data"])

                # Prepare the Transaction struct as required by the Solidity contract
                transaction_struct = (
                    encrypted_extended_data,  # extended_data
                    transact_dt,  # transact_dt
                    int(Decimal(transaction["transact_amt"]) * 100),  # transact_amt
                    int(Decimal(transaction["service_fee_amt"]) * 100),  # service_fee_amt
                    int(Decimal(transaction["advance_amt"]) * 100),  # advance_amt
                    encrypted_transact_data,  # transact_data
                    advance_pay_dt,  # advance_pay_dt
                    int(Decimal(transaction["advance_pay_amt"]) * 100),  # advance_pay_amt
                    transaction["advance_confirm"]  # advance_confirm
                )

                # Get the current nonce
                nonce = self.w3.eth.get_transaction_count(self.config["wallet_addr"])

                # Build the transaction to call importTransaction
                transaction_tx = self.w3_contract.functions.importTransaction(
                    contract_idx,  # The index of the contract
                    transaction_struct  # The transaction struct
                ).build_transaction({
                    "from": self.config["wallet_addr"],
                    "nonce": nonce
                })

                # Estimate the gas required for the transaction
                estimated_gas = self.w3.eth.estimate_gas(transaction_tx)
                self.logger.info(f"Estimated gas for importTransaction: {estimated_gas}")

                # Set gas limit dynamically based on estimated gas or config
                gas_limit = max(estimated_gas, self.config["gas_limit"])
                self.logger.info(f"Final gas limit: {gas_limit}")

                # Add the gas limit to the transaction
                transaction_tx["gas"] = gas_limit

                # Send the transaction
                tx_receipt = self.w3_manager.get_tx_receipt(transaction_tx)
                if tx_receipt["status"] != 1:
                    raise RuntimeError(f"Blockchain transaction failed for contract {contract_idx} transaction.")

            return True

        except Exception as e:
            self.logger.error(f"Error importing transactions for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to import transactions for contract {contract_idx}") from e

    # Usage Example:
    # transactions_api = TransactionsAPI()
    # transactions_api.get_transactions(contract_idx=123)