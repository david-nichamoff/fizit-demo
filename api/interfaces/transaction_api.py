import datetime
import logging
import json
from decimal import Decimal
from json_logic import jsonLogic

from api.managers import Web3Manager, ConfigManager
from api.interfaces import ContractAPI
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
        return None if ts == 0 else datetime.datetime.fromtimestamp(ts)

    def get_transact_dict(self, transact, transact_idx, contract):
        try:
            transact_dict = {
                "extended_data": json.loads(transact[0].replace("'", '"')),
                "transact_dt": self.from_timestamp(transact[1]),
                "transact_amt": f'{Decimal(transact[2]) / 100:.2f}',
                "service_fee_amt": f'{Decimal(transact[3]) / 100:.2f}',
                "advance_amt": f'{Decimal(transact[4]) / 100:.2f}',
                "transact_data": json.loads(transact[5].replace("'", '"')),
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

    def get_transactions(self, contract_idx, transact_min_dt=None, transact_max_dt=None):
        try:
            transactions = []
            contract = self.contract_api.get_contract(contract_idx)

            transacts = self.w3_contract.functions.getTransactions(contract['contract_idx']).call()
            for transact in transacts:
                transact_dict = self.get_transact_dict(transact, len(transactions), contract)
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

    def add_transactions(self, contract_idx, transact_logic, transactions):
        self.validate_transactions(transactions)

        try:
            for transaction in transactions:
                extended_data = str(transaction["extended_data"])
                transact_dt = int(transaction["transact_dt"].timestamp())
                transact_data = transaction["transact_data"]

                # Check if 'adj' is in transact_data for adjustment
                if "adj" in transact_data:
                    transact_amt = int(Decimal(transact_data["adj"]) * 100)
                else:
                    transact_amt = int(jsonLogic(transact_logic, transact_data) * 100)

                nonce = self.w3.eth.get_transaction_count(self.config["wallet_addr"])

                # Build the transaction
                call_function = self.w3_contract.functions.addTransaction(
                    contract_idx, extended_data, transact_dt, transact_amt, str(transact_data)
                ).build_transaction({
                    "from": self.config["wallet_addr"],
                    "nonce": nonce
                })

                # Estimate the gas required for the transaction
                estimated_gas = self.w3.eth.estimate_gas(call_function)
                self.logger.info(f"Estimated gas for addTransaction: {estimated_gas}")

                # Set gas limit dynamically based on estimated gas or config
                gas_limit = max(estimated_gas, self.config["gas_limit"])
                self.logger.info(f"Final gas limit: {gas_limit}")

                # Add the gas limit to the transaction
                call_function["gas"] = gas_limit

                # Send the transaction
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

# Usage Example:
# transactions_api = TransactionsAPI()
# transactions_api.get_transactions(contract_idx=123)