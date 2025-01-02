import datetime
import logging
import json

from datetime import timezone, datetime, time
from decimal import Decimal

from api.managers import Web3Manager, ConfigManager
from api.interfaces import ContractAPI

from api.interfaces.encryption_api import get_encryptor, get_decryptor
from .util_api import is_valid_json

class SettlementAPI:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure that the class is a singleton."""
        if not cls._instance:
            cls._instance = super(SettlementAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.w3_manager = Web3Manager()
        self.w3 = self.w3_manager.get_web3_instance()
        self.w3_contract = self.w3_manager.get_web3_contract()
        self.contract_api = ContractAPI()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

        self.wallet_addr = self.config_manager.get_nested_config_value("wallet_addr", "Transactor")
        self.checksum_wallet_addr = self.w3_manager.get_checksum_address(self.wallet_addr)

    def from_timestamp(self, ts):
        return None if ts == 0 else datetime.fromtimestamp(ts, tz=timezone.utc)

    def get_settle_dict(self, settle, settle_idx, contract, api_key, parties):
        decryptor = get_decryptor(api_key, parties)

        try:
            decrypted_extended_data = decryptor.decrypt(settle[0])

            settle_dict = {
                "extended_data": decrypted_extended_data, 
                "settle_due_dt": self.from_timestamp(settle[1]),
                "transact_min_dt": self.from_timestamp(settle[2]),
                "transact_max_dt": self.from_timestamp(settle[3]),
                "transact_count": settle[4],
                "advance_amt": f'{Decimal(settle[5]) / 100:.2f}',
                "advance_amt_gross": f'{Decimal(settle[6]) / 100:.2f}',
                "settle_pay_dt": self.from_timestamp(settle[7]),
                "settle_exp_amt": f'{Decimal(settle[8]) / 100:.2f}',
                "settle_pay_amt": f'{Decimal(settle[9]) / 100:.2f}',
                "settle_tx_hash": settle[10],
                "dispute_amt": f'{Decimal(settle[11]) / 100:.2f}',
                "dispute_reason": settle[12],
                "days_late": settle[13],
                "late_fee_amt": f'{Decimal(settle[14]) / 100:.2f}',
                "residual_pay_dt": self.from_timestamp(settle[15]),
                "residual_pay_amt": f'{Decimal(settle[16]) / 100:.2f}',
                "residual_exp_amt": f'{Decimal(settle[17]) / 100:.2f}',
                "residual_calc_amt": f'{Decimal(settle[18]) / 100:.2f}',
                "residual_tx_hash": settle[19],
                "contract_idx": contract['contract_idx'],
                "contract_name": contract['contract_name'],
                "funding_instr": contract['funding_instr'],
                "deposit_instr": contract['deposit_instr'],
                "settle_idx": settle_idx
            }

            self.logger.debug("Settle exp amount (String): %s", settle_dict["settle_exp_amt"])
            self.logger.debug("Settle exp type: %s", type(settle_dict["settle_exp_amt"]))

            return settle_dict

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decoding error for settlement {settle_idx}: {str(e)}")
            raise RuntimeError(f"Failed to decode JSON for settlement {settle_idx}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error processing settlement {settle_idx}: {str(e)}")
            raise RuntimeError(f"Failed to process settlement {settle_idx}") from e

    def get_settlements(self, contract_idx, api_key=None, parties=[]):
        try:
            settlements = []
            contract = self.contract_api.get_contract(contract_idx, api_key, parties)
            settles = self.w3_contract.functions.getSettlements(contract['contract_idx']).call()

            for settle_idx, settle in enumerate(settles):
                settle_dict = self.get_settle_dict(settle, settle_idx, contract, api_key, parties)
                settlements.append(settle_dict)

            return sorted(settlements, key=lambda d: d['settle_due_dt'], reverse=True)

        except Exception as e:
            self.logger.error(f"Error retrieving settlements for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to retrieve settlements for contract {contract_idx}") from e

    def add_settlements(self, contract_idx, settlements):
        self.validate_settlements(settlements)

        try:
            encryptor = get_encryptor()

            for settlement in settlements:
                due_dt = int(settlement["settle_due_dt"].timestamp())
                min_dt = int(settlement["transact_min_dt"].timestamp())
                max_dt = int(settlement["transact_max_dt"].timestamp())
                
                # Encrypt sensitive fields before sending to the blockchain
                encrypted_extended_data = encryptor.encrypt(settlement["extended_data"])

                # Build the transaction
                transaction = self.w3_contract.functions.addSettlement(
                    contract_idx, encrypted_extended_data, due_dt, min_dt, max_dt
                ).build_transaction()

                # Send the transaction
                tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")

                if tx_receipt["status"] != 1:
                    raise RuntimeError(f"Blockchain transaction failed for contract {contract_idx} settlement.")

            return True

        except Exception as e:
            self.logger.error(f"Error adding settlements for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to add settlements for contract {contract_idx}") from e
            
    def delete_settlements(self, contract_idx):
        try:
            # Build the transaction
            transaction = self.w3_contract.functions.deleteSettlements(contract_idx).build_transaction()
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")

            if tx_receipt["status"] != 1:
                raise RuntimeError(f"Blockchain transaction failed for deleting settlements in contract {contract_idx}.")

            return True

        except Exception as e:
            self.logger.error(f"Error deleting settlements for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to delete settlements for contract {contract_idx}") from e

    def validate_settlements(self, settlements):
        try:
            for settlement in settlements:
                if settlement['transact_min_dt'] >= settlement['transact_max_dt']:
                    raise ValueError(f"Transaction minimum date must be less than maximum date. "
                                     f"Found: transact_min_dt={settlement['transact_min_dt']}, "
                                     f"transact_max_dt={settlement['transact_max_dt']}")

                if settlement['transact_max_dt'] > settlement['settle_due_dt']:
                    raise ValueError(f"Transaction maximum date must be less than or equal to settlement due date. "
                                     f"Found: transact_max_dt={settlement['transact_max_dt']}, "
                                     f"settle_due_dt={settlement['settle_due_dt']}")

                if not is_valid_json(settlement["extended_data"]):
                    raise ValueError(f"Invalid JSON for 'extended_data': '{settlement['extended_data']}'.")

        except ValueError as e:
            self.logger.error(f"Validation error in settlements: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during settlements validation: {str(e)}")
            raise

    def import_settlements(self, contract_idx, settlements):
        """
        Import settlements to a given contract using the Solidity importSettlement function.
        This function loads historical data by passing Settlement struct directly.
        
        :param contract_idx: The index of the contract to which the settlements will be imported.
        :param settlements: List of settlement dictionaries to be imported.
        """
        try:
            encryptor = get_encryptor()

            for settlement in settlements:
                # Convert datetime fields from string to datetime object, then to Unix timestamps
                due_dt = int(datetime.fromisoformat(settlement["settle_due_dt"]).timestamp())
                min_dt = int(datetime.fromisoformat(settlement["transact_min_dt"]).timestamp())
                max_dt = int(datetime.fromisoformat(settlement["transact_max_dt"]).timestamp())
                pay_dt = int(datetime.fromisoformat(settlement["settle_pay_dt"]).timestamp()) if settlement["settle_pay_dt"] else 0
                residual_pay_dt = int(datetime.fromisoformat(settlement["residual_pay_dt"]).timestamp()) if settlement["residual_pay_dt"] else 0

                # Encrypt sensitive fields like extended_data
                encrypted_extended_data = encryptor.encrypt(settlement["extended_data"])

                # Prepare the Settlement struct as required by the Solidity contract
                settlement_struct = (
                    encrypted_extended_data,  # extended_data
                    due_dt,  # settle_due_dt
                    min_dt,  # transact_min_dt
                    max_dt,  # transact_max_dt
                    settlement["transact_count"],  # transact_count
                    int(Decimal(settlement["advance_amt"]) * 100),  # advance_amt
                    int(Decimal(settlement["advance_amt_gross"]) * 100),  # advance_amt_gross
                    pay_dt,  # settle_pay_dt
                    int(Decimal(settlement["settle_exp_amt"]) * 100),  # settle_exp_amt
                    int(Decimal(settlement["settle_pay_amt"]) * 100),  # settle_pay_amt
                    int(Decimal(settlement["dispute_amt"]) * 100),  # dispute_amt
                    settlement["dispute_reason"],  # dispute_reason
                    settlement["days_late"],  # days_late
                    int(Decimal(settlement["late_fee_amt"]) * 100),  # late_fee_amt
                    residual_pay_dt,  # residual_pay_dt
                    int(Decimal(settlement["residual_pay_amt"]) * 100),  # residual_pay_amt
                    int(Decimal(settlement["residual_exp_amt"]) * 100),  # residual_exp_amt
                    int(Decimal(settlement["residual_calc_amt"]) * 100),  # residual_calc_amt
                )

                # Build the transaction to call importSettlement
                transaction = self.w3_contract.functions.importSettlement(
                    contract_idx,  # The index of the contract
                    settlement_struct  # The settlement struct
                ).build_transaction()

                # Send the transaction
                tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")

                if tx_receipt["status"] != 1:
                    raise RuntimeError(f"Blockchain transaction failed for contract {contract_idx} settlement.")

            return True

        except Exception as e:
                self.logger.error(f"Error importing settlements for contract {contract_idx}: {str(e)}")
                raise RuntimeError(f"Failed to import settlements for contract {contract_idx}") from e