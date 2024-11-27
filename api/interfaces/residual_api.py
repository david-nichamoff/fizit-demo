import datetime
from decimal import Decimal
import logging

from datetime import timezone

from api.managers import Web3Manager, ConfigManager
from api.interfaces import SettlementAPI, ContractAPI, PartyAPI
from api.adapters.bank import MercuryAdapter, TokenAdapter

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
            self.party_api = PartyAPI()

            self.mercury_adapter = MercuryAdapter()
            self.token_adapter = TokenAdapter()

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
            parties = self.party_api.get_parties(contract_idx)

            for settle in settlements:
                if settle["residual_pay_amt"] == "0.00" and Decimal(settle["residual_calc_amt"]) > Decimal(0.00):

                    for party in parties:
                        if party.get("party_type") == "seller":
                            recipient_addr = party.get("party_addr")
                        elif party.get("party_type") == "funder":
                            funder_addr = party.get("party_addr") 

                    # Core fields that must exist
                    residual_dict = {
                        "contract_idx": contract["contract_idx"],
                        "settle_idx": settle["settle_idx"],
                        "bank": contract["funding_instr"]["bank"],
                        "recipient_addr":  recipient_addr,
                        "funder_addr": funder_addr,
                        "residual_calc_amt": settle["residual_calc_amt"]
                    }

                    # Conditionally add optional fields
                    if contract["funding_instr"].get("account_id"):
                        residual_dict["account_id"] = contract["funding_instr"]["account_id"]
                    
                    if contract["funding_instr"].get("recipient_id"):
                        residual_dict["recipient_id"] = contract["funding_instr"]["recipient_id"]

                    if contract["funding_instr"].get("token_symbol"):
                        residual_dict["token_symbol"] = contract["funding_instr"]["token_symbol"]

                    residuals.append(residual_dict)

            return residuals

        except Exception as e:
            self.logger.error(f"Error retrieving residuals for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to retrieve residuals for contract {contract_idx}") from e

    def add_residuals(self, contract_idx, residuals):

        for residual in residuals:
            try:
                if residual["bank"] == "mercury":
                    # Use the MercuryAdapter to make the payment
                    success, error_message = self.mercury_adapter.make_payment(
                        residual["account_id"], residual["recipient_id"], residual["residual_calc_amt"]
                    )
                    if not success:
                        self.logger.error(f"Payment failed for contract {contract_idx}, settlement {residual['settle_idx']}: {error_message}")
                        raise ValueError(f"Payment failed: {error_message}")
                    
                elif residual["bank"] == "token":
                    # Use the TokenAdapter to make the payment
                    self.logger.info(f"residual: {residual}")
                    success, error_message = self.token_adapter.make_payment(
                        residual["contract_idx"], residual["funder_addr"], residual["recipient_addr"], residual["token_symbol"], residual["residual_calc_amt"]
                    )
                    if not success:
                        self.logger.error(f"Token transfer failed for contract {contract_idx}, settlement {residual['settle_idx']}: {error_message}")
                        raise ValueError(f"Token transfer failed: {error_message}")

                else:
                    # Unsupported bank type
                    self.logger.error(f"Unsupported bank type {residual["bank"]} for contract {contract_idx}")
                    raise ValueError(f"Unsupported bank type: {residual["bank"]}")

                # Blockchain transaction for paying residuals
                nonce = self.w3.eth.get_transaction_count(self.checksum_wallet_addr)
                current_time = int(datetime.datetime.now().timestamp())
                payment_amt = int(Decimal(residual["residual_calc_amt"]) * 100)

                # Build the blockchain transaction
                transaction = self.w3_contract.functions.payResidual(
                    contract_idx, residual["settle_idx"], current_time, payment_amt
                ).build_transaction({
                    "from": self.checksum_wallet_addr,
                    "nonce": nonce
                })

                # Send the blockchain transaction
                tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")

                if tx_receipt["status"] != 1:
                    self.logger.error(f"Blockchain transaction failed for contract {contract_idx}, settlement {residual['settle_idx']}.")
                    raise RuntimeError("Transaction failed on the blockchain.")

            except AttributeError as e:
                self.logger.error(f"Error processing residual {residual['settle_idx']} for contract {contract_idx}: {str(e)}")
                raise RuntimeError(f"Failed to process residual {residual['settle_idx']} for contract {contract_idx}") from e

        return True