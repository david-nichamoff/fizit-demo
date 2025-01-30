import logging
from decimal import Decimal

from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.web3 import Web3Manager
from api.config import ConfigManager
from api.registry import RegistryManager
from api.interfaces.encryption_api import get_encryptor, get_decryptor
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning
from api.utilities.formatting import from_timestamp, to_decimal

class SettlementAPI(ResponseMixin):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure the class is a singleton."""
        if not cls._instance:
            cls._instance = super(SettlementAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize SettlementAPI with necessary dependencies."""
        if not hasattr(self, "initialized"):
            self.registry_manager = RegistryManager()
            self.config_manager = ConfigManager()
            self.w3_manager = Web3Manager()

            self.wallet_addr = self.config_manager.get_wallet_address("Transactor")
            self.logger = logging.getLogger(__name__)
            self.initialized = True

    def get_settlements(self, contract_type, contract_idx, api_key=None, parties=[]):
        """Retrieve all settlements for a given contract."""
        try:
            contract_api = self.registry_manager.get_contract_api(contract_type)
            response = contract_api.get_contract(contract_type, contract_idx, api_key, parties)
            if response["status"] == status.HTTP_200_OK:
                contract = response["data"]
                log_info(self.logger, f"Retrieved {contract_type}:{contract_idx} with data {contract}")
            else:
                raise RuntimeError("Error retrieving contract")

            w3_contract = self.w3_manager.get_web3_contract(contract_type)
            raw_settlements = w3_contract.functions.getSettlements(contract["contract_idx"]).call()
            log_info(self.logger, f"Retrieved settlements {raw_settlements} for {contract_type}:{contract_idx}")

            settlements = []
            for idx, settlement in enumerate(raw_settlements):
                settlement_dict = self._build_settlement_dict(settlement, idx, contract_type, contract, api_key, parties)
                settlements.append(settlement_dict)

            success_message = f"Retrieved {len(settlements)} settlements for {contract_type}:{contract_idx}"
            data = sorted(settlements, key=lambda d: d["settle_due_dt"], reverse=True)
            return self._format_success(data, success_message, status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Validation error returning settlements for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error retrieving settlements for {contract_type}:{contract_idx}: {e}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_settlements(self, contract_type, contract_idx, settlements):
        """Add settlements to the blockchain for a given contract."""
        try:
            encryptor = get_encryptor()
            processed_count = 0

            for settlement in settlements:
                transaction = self._build_add_settlement_transaction(contract_type, contract_idx, settlement, encryptor)
                tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_type, contract_idx, "fizit")

                if tx_receipt["status"] != 1:
                    raise RuntimeError

                processed_count += 1

            success_message = f"Successfully added {processed_count} settlements for {contract_type}:{contract_idx}"
            return self._format_success({"count":processed_count}, success_message, status.HTTP_201_CREATED )

        except ValidationError as e:
            error_message = f"Validation error for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error adding settlements for {contract_type}:{contract_idx}: {e}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete_settlements(self, contract_type, contract_idx):
        """Delete all settlements for a given contract."""
        try:
            w3_contract = self.w3_manager.get_web3_contract(contract_type)
            transaction = w3_contract.functions.deleteSettlements(contract_idx).build_transaction()
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")

            if tx_receipt["status"] != 1:
                raise RuntimeError

            success_message = f"All settlements deleted for {contract_type}:{contract_idx}"
            return self._format_success({"contract_idx" : contract_idx}, success_message, status.HTTP_204_NO_CONTENT)

        except ValidationError as e:
            error_message = f"Validation error for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error deleting settlements for {contract_type}:{contract_idx}: {e}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _build_settlement_dict(self, settle, idx, contract_type, contract, api_key, parties):
        """Build a settlement dictionary from raw data."""
        try:
            decryptor = get_decryptor(api_key, parties)
            decrypted_extended_data = decryptor.decrypt(settle[0])

            return {
                "extended_data": decrypted_extended_data,
                "settle_due_dt": from_timestamp(settle[1]),
                "transact_min_dt": from_timestamp(settle[2]),
                "transact_max_dt": from_timestamp(settle[3]),
                "transact_count": settle[4],
                "advance_amt": to_decimal(settle[5]),
                "advance_amt_gross": to_decimal(settle[6]),
                "settle_pay_dt": from_timestamp(settle[7]),
                "settle_exp_amt": to_decimal(settle[8]),
                "settle_pay_amt": to_decimal(settle[9]),
                "settle_tx_hash": settle[10],
                "dispute_amt": to_decimal(settle[11]),
                "dispute_reason": settle[12],
                "days_late": settle[13],
                "late_fee_amt": to_decimal(settle[14]),
                "residual_pay_dt": from_timestamp(settle[15]),
                "residual_pay_amt": to_decimal(settle[16]),
                "residual_exp_amt": to_decimal(settle[17]),
                "residual_calc_amt": to_decimal(settle[18]),
                "residual_tx_hash": settle[19],
                "contract_type": contract_type,
                "contract_idx": contract["contract_idx"],
                "contract_name": contract["contract_name"],
                "funding_instr": contract["funding_instr"],
                "deposit_instr": contract["deposit_instr"],
                "settle_idx": idx
            }
        except Exception as e:
            error_message = f"Error building settlement dictionary for settlement {idx}: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _build_add_settlement_transaction(self, contract_type, contract_idx, settlement, encryptor):
        """Build the transaction to add a settlement."""
        try:
            encrypted_data = encryptor.encrypt(settlement["extended_data"])
            due_dt = int(settlement["settle_due_dt"].timestamp())
            min_dt = int(settlement["transact_min_dt"].timestamp())
            max_dt = int(settlement["transact_max_dt"].timestamp())

            w3_contract = self.w3_manager.get_web3_contract(contract_type)
            return w3_contract.functions.addSettlement(
                contract_idx, encrypted_data, due_dt, min_dt, max_dt
            ).build_transaction()
        except Exception as e:
            error_message = f"Error building settlement transaction for {contract_type}:{contract_idx}: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

