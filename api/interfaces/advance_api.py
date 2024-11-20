import datetime
import logging
from decimal import Decimal

from datetime import timezone

from api.managers import ConfigManager, Web3Manager
from api.interfaces import TransactionAPI, ContractAPI
from api.adapters.bank import MercuryAdapter, TokenAdapter

from eth_utils import to_checksum_address

class AdvanceAPI:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure that the class is a singleton."""
        if not cls._instance:
            cls._instance = super(AdvanceAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.w3_manager = Web3Manager()
        self.w3 = self.w3_manager.get_web3_instance()
        self.transaction_api = TransactionAPI()
        self.contract_api = ContractAPI()

        self.mercury_adapter = MercuryAdapter()
        self.token_adapter = TokenAdapter()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

        self.wallet_addr = self.config_manager.get_nested_config_value("wallet_addr", "Transactor")
        self.checksum_wallet_addr = to_checksum_address(self.wallet_addr)

    def from_timestamp(self, ts):
        return None if ts == 0 else datetime.datetime.fromtimestamp(ts, tz=timezone.utc)

    def get_advances(self, contract_idx):
        advances = []
        transactions = self.transaction_api.get_transactions(contract_idx)
        contract = self.contract_api.get_contract(contract_idx)

        for transact in transactions:
            self.logger.info(f"{transact}")
            self.logger.info(f"{contract}")
            if transact["advance_pay_amt"] == "0.00" and Decimal(transact["advance_amt"]) > Decimal(0.00):
                advance_dict = {
                    "contract_idx": contract["contract_idx"],
                    "transact_idx": transact["transact_idx"],
                    "bank": contract["funding_instr"]["bank"],
                    "account_id": contract["funding_instr"].get("account_id"),
                    "recipient_id": contract["funding_instr"].get("recipient_id"),
                    "advance_amt": transact["advance_amt"]
                }
                advances.append(advance_dict)

        return advances

    def add_advances(self, contract_idx, advances):
        contract = self.contract_api.get_contract(contract_idx)
        self.logger.info(f"advances {advances}")
        self.logger.info(f"contract {contract}")

        for advance in advances:
            try:
                if advance["bank"] == "mercury":
                    # Directly use the mercury_adapter to make the payment
                    success, error_message = self.mercury_adapter.make_payment(
                        advance["account_id"], advance["recipient_id"], advance["advance_amt"]
                    )
                    if not success:
                        self.logger.error(f"Payment failed for contract {contract_idx}, transaction {advance['transact_idx']}: {error_message}")
                        raise ValueError(f"Payment failed: {error_message}")
                 
                elif advance["bank"] == "token":
                    # Use the token_adapter to make the payment
                    funder_wallet = contract["parties"]["funder"]["wallet_addr"]
                    recipient_wallet = contract["parties"]["seller"]["wallet_addr"]
                    self.logger.info(f"funder_wallet {recipient_wallet}")
                    success, error_message = self.token_adapter.make_payment(
                        funder_wallet, recipient_wallet, advance["token"], advance["advance_amt"]
                    )
                    if not success:
                        self.logger.error(f"Token transfer failed for contract {contract_idx}, transaction {advance['transact_idx']}: {error_message}")
                        raise ValueError(f"Token transfer failed: {error_message}")
                else:
                    self.logger.error(f"Unsupported bank type {advance['bank']} for contract {contract_idx}")
                    raise ValueError(f"Unsupported bank type: {advance['bank']}")

                nonce = self.w3_manager.get_web3_instance().eth.get_transaction_count(self.checksum_wallet_addr)
                current_time = int(datetime.datetime.now().timestamp())
                payment_amt = int(Decimal(advance["advance_amt"]) * 100)

                # Build the transaction
                transaction = self.w3_manager.get_web3_contract().functions.payAdvance(
                    contract_idx, advance["transact_idx"], current_time, payment_amt, "completed"
                ).build_transaction({
                    "from": self.checksum_wallet_addr,
                    "nonce": nonce
                })

                tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr)

                if tx_receipt["status"] != 1:
                    self.logger.error(f"Blockchain transaction failed for contract {contract_idx}, transaction {advance['transact_idx']}.")
                    raise RuntimeError("Transaction failed on the blockchain.")

            except AttributeError as e:
                self.logger.error(f"Bank adapter error for contract {contract_idx}, transaction {advance['transact_idx']}: {str(e)}")
                raise RuntimeError(f"Bank adapter error: {str(e)}")

        return True

# Usage example:
# advance_api = AdvanceAPI()
# advances = advance_api.get_advances(contract_idx)
# advance_api.add_advances(contract_idx, advances)
