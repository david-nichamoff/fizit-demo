import datetime
from decimal import Decimal
import logging

from datetime import timezone

from api.managers import Web3Manager, ConfigManager
from api.interfaces import SettlementAPI, ContractAPI
from api.adapters.bank import MercuryAdapter
from eth_utils import to_checksum_address

class ResidualAPI:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure that the class is a singleton."""
        if not cls._instance:
            cls._instance = super(ResidualAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):  # Ensure init runs only once
            self.config_manager = ConfigManager()
            self.config = self.config_manager.load_config()
            self.w3_manager = Web3Manager()
            self.w3 = self.w3_manager.get_web3_instance()
            self.w3_contract = self.w3_manager.get_web3_contract()
            self.settlement_api = SettlementAPI()
            self.contract_api = ContractAPI()

            self.mercury_adapter = MercuryAdapter()

            self.logger = logging.getLogger(__name__)
            self.initialized = True  # Mark this instance as initialized

            self.wallet_addr = self.config_manager.get_nested_config_value("wallet_addr", "Transactor")
            self.checksum_wallet_addr = to_checksum_address(self.wallet_addr)

    def from_timestamp(self, ts):
        return None if ts == 0 else datetime.datetime.fromtimestamp(ts, tz=timezone.utc)

    def get_residuals(self, contract_idx):
        """Retrieve the residuals for a given contract."""
        try:
            residuals = []
            settlements = self.settlement_api.get_settlements(contract_idx)
            contract = self.contract_api.get_contract(contract_idx)

            for settle in settlements:
                if settle["residual_pay_amt"] == "0.00" and Decimal(settle["residual_calc_amt"]) > Decimal(0.00):
                    residual_dict = {
                        "contract_idx": contract["contract_idx"],
                        "settle_idx": settle["settle_idx"],
                        "bank": contract["funding_instr"]["bank"],
                        "account_id": contract["funding_instr"]["account_id"],
                        "recipient_id": contract["funding_instr"]["recipient_id"],
                        "residual_calc_amt": settle["residual_calc_amt"]
                    }
                    residuals.append(residual_dict)

            return residuals

        except Exception as e:
            self.logger.error(f"Error retrieving residuals for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to retrieve residuals for contract {contract_idx}") from e

    def add_residuals(self, contract_idx, residuals):
        """Add residuals for a contract."""
        if not residuals:
            return True

        try:
            contract = self.contract_api.get_contract(contract_idx)

            for residual in residuals:
                try:
                    # Directly use MercuryAdapter for payments, no dynamic adapter lookup
                    success, error_message = self.mercury_adapter.make_payment(
                        residual["account_id"], residual["recipient_id"], residual["residual_calc_amt"]
                    )

                    if not success:
                        raise ValueError(f"Payment failed: {error_message}")

                    # Blockchain transaction for paying residuals
                    nonce = self.w3.eth.get_transaction_count(self.checksum_wallet_addr)
                    current_time = int(datetime.datetime.now().timestamp())
                    payment_amt = int(Decimal(residual["residual_calc_amt"]) * 100)

                    # Build the transaction
                    transaction = self.w3_contract.functions.payResidual(
                        contract_idx, residual["settle_idx"], current_time, payment_amt
                    ).build_transaction({
                        "from": self.checksum_wallet_addr,
                        "nonce": nonce
                    })

                    # Send the transaction
                    tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")

                    if tx_receipt["status"] != 1:
                        raise RuntimeError("Transaction failed on the blockchain.")

                except Exception as e:
                    self.logger.error(f"Error processing residual {residual['settle_idx']} for contract {contract_idx}: {str(e)}")
                    raise RuntimeError(f"Failed to process residual {residual['settle_idx']} for contract {contract_idx}") from e

            return True

        except Exception as e:
            self.logger.error(f"Error adding residuals for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to add residuals for contract {contract_idx}") from e