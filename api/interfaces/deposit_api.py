import datetime
import logging
from decimal import Decimal

from datetime import timezone

from api.adapters.bank import MercuryAdapter
from api.managers import Web3Manager, ConfigManager
from api.interfaces import ContractAPI, TransactionAPI
from eth_utils import to_checksum_address

class DepositAPI:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure the class is a singleton."""
        if not cls._instance:
            cls._instance = super(DepositAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize the class with config, web3, and logger."""
        if not hasattr(self, 'initialized'):  # Ensure that init runs only once
            self.config_manager = ConfigManager()
            self.config = self.config_manager.load_config()
            self.w3_manager = Web3Manager()
            self.w3 = self.w3_manager.get_web3_instance()
            self.w3_contract = self.w3_manager.get_web3_contract()
            self.transaction_api = TransactionAPI()
            self.contract_api = ContractAPI()

            self.mercury_adapter = MercuryAdapter()

            self.logger = logging.getLogger(__name__)
            self.initialized = True  # Mark this instance as initialized

            self.wallet_addr = self.config_manager.get_nested_config_value("wallet_addr", "Transactor")
            self.checksum_wallet_addr = to_checksum_address(self.wallet_addr)

    def from_timestamp(self, ts):
        return None if ts == 0 else datetime.datetime.fromtimestamp(ts, tz=timezone.utc)

    def get_deposits(self, start_date, end_date, contract_idx):
        """Retrieve deposits from the bank adapter for a given contract."""
        try:
            contract = self.contract_api.get_contract(contract_idx)

            # Directly call the mercury adapter to get deposits
            deposits = self.mercury_adapter.get_deposits(start_date, end_date, contract)
            return deposits
        except Exception as e:
            self.logger.error(f"Error retrieving deposits for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to retrieve deposits for contract {contract_idx}") from e

    def add_deposits(self, contract_idx, deposits):
        """Post deposits to the blockchain as part of the contract settlement."""
        try:
            contract = self.contract_api.get_contract(contract_idx)

            for deposit in deposits:
                print(deposit)
                try:
                    # Convert deposit_amt to an integer representing cents
                    payment_amt = int(Decimal(deposit["deposit_amt"]) * 100)

                    # Use deposit_dt and set the time to midnight UTC
                    settlement_date = deposit["deposit_dt"].replace(hour=0, minute=0, second=0, microsecond=0)
                    settlement_timestamp = int(settlement_date.timestamp())

                    # Extract the necessary values
                    settle_idx = deposit["settle_idx"]
                    dispute_reason = deposit["dispute_reason"]

                    nonce = self.w3.eth.get_transaction_count(self.checksum_wallet_addr)

                    # Build the transaction
                    transaction = self.w3_contract.functions.postSettlement(
                        contract_idx, settle_idx, settlement_timestamp, payment_amt, dispute_reason
                    ).build_transaction({
                        "from": self.checksum_wallet_addr,
                        "nonce": nonce
                    })

                    # Send the transaction
                    tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")

                    if tx_receipt["status"] != 1:
                        raise RuntimeError(f"Transaction failed with status: {tx_receipt['status']}")

                except Exception as e:
                    self.logger.error(f"Error in add_deposits for contract {contract_idx}: {str(e)}")
                    raise RuntimeError(f"Failed to add deposit {deposit['deposit_id']} for contract {contract_idx}") from e

        except Exception as e:
            self.logger.error(f"Error in add_deposits for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to add deposits for contract {contract_idx}") from e

        return True