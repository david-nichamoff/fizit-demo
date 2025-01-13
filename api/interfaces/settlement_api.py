import logging
from decimal import Decimal

from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.managers import Web3Manager, ConfigManager
from api.interfaces import ContractAPI
from api.interfaces.encryption_api import get_encryptor, get_decryptor

from api.mixins import ValidationMixin, AdapterMixin, InterfaceResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning
from api.utilities.formatting import from_timestamp, to_decimal
from api.utilities.validation import is_valid_json

class SettlementAPI(ValidationMixin, InterfaceResponseMixin):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure the class is a singleton."""
        if not cls._instance:
            cls._instance = super(SettlementAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize SettlementAPI with necessary dependencies."""
        if not hasattr(self, "initialized"):
            self.config_manager = ConfigManager()
            self.config = self.config_manager.load_config()
            self.w3_manager = Web3Manager()
            self.w3_contract = self.w3_manager.get_web3_contract()
            self.contract_api = ContractAPI()

            self.wallet_addr = self.config_manager.get_nested_config_value("wallet_addr", "Transactor")
            self.logger = logging.getLogger(__name__)
            self.initialized = True

    def get_settlements(self, contract_idx, api_key=None, parties=[]):
        """Retrieve all settlements for a given contract."""
        try:
            self._validate_contract_idx(contract_idx, self.contract_api)

            settlements = []

            response = self.contract_api.get_contract(contract_idx, api_key, parties)
            if response["status"] == status.HTTP_200_OK:
                contract = response["data"]
                log_info(self.logger, f"Retrieved contract {contract_idx} with data {contract}")
            else:
                raise RuntimeError("Error retrieving contract")

            raw_settlements = self.w3_contract.functions.getSettlements(contract["contract_idx"]).call()
            log_info(self.logger, f"Retrieved settlements {raw_settlements} for contract {contract_idx}")

            for idx, settlement in enumerate(raw_settlements):
                settlement_dict = self._build_settlement_dict(settlement, idx, contract, api_key, parties)
                settlements.append(settlement_dict)

            success_message = f"Retrieved {len(settlements)} settlements for contract {contract_idx}"
            data = sorted(settlements, key=lambda d: d["settle_due_dt"], reverse=True)
            return self._format_success(data, success_message, status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Validation error returning settlements for {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error retrieving settlements for contract {contract_idx}: {e}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_settlements(self, contract_idx, settlements):
        """Add settlements to the blockchain for a given contract."""
        try:
            self._validate_contract_idx(contract_idx, self.contract_api)

            self._validate_settlements(settlements)
            encryptor = get_encryptor()
            processed_count = 0

            for settlement in settlements:
                transaction = self._build_add_settlement_transaction(contract_idx, settlement, encryptor)
                tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")

                if tx_receipt["status"] != 1:
                    raise RuntimeError

                processed_count += 1

            success_message = f"Successfully added {processed_count} settlements for contract {contract_idx}"
            return self._format_success({"count":processed_count}, success_message, status.HTTP_201_CREATED )

        except ValidationError as e:
            error_message = f"Validation error for {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error adding settlements for contract {contract_idx}: {e}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete_settlements(self, contract_idx):
        """Delete all settlements for a given contract."""
        try:
            self._validate_contract_idx(contract_idx, self.contract_api)

            transaction = self.w3_contract.functions.deleteSettlements(contract_idx).build_transaction()
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")

            if tx_receipt["status"] != 1:
                raise RuntimeError

            success_message = "All settlements deleted for contract {contract_idx}"
            return self._format_success({"contract_idx" : contract_idx}, success_message, status.HTTP_204_NO_CONTENT)

        except ValidationError as e:
            error_message = f"Validation error for {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error deleting settlements for contract {contract_idx}: {e}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _build_settlement_dict(self, settle, idx, contract, api_key, parties):
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

    def _build_add_settlement_transaction(self, contract_idx, settlement, encryptor):
        """Build the transaction to add a settlement."""
        try:
            encrypted_data = encryptor.encrypt(settlement["extended_data"])
            due_dt = int(settlement["settle_due_dt"].timestamp())
            min_dt = int(settlement["transact_min_dt"].timestamp())
            max_dt = int(settlement["transact_max_dt"].timestamp())

            return self.w3_contract.functions.addSettlement(
                contract_idx, encrypted_data, due_dt, min_dt, max_dt
            ).build_transaction()
        except Exception as e:
            error_message = f"Error building settlement transaction for contract {contract_idx}: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _validate_settlements(self, settlements):
        """Validate settlements before adding them to the blockchain."""
        try:
            for settlement in settlements:
                if settlement["transact_min_dt"] >= settlement["transact_max_dt"]:
                    raise ValidationError(f"Minimum transaction date must be before maximum transaction date.")
                if settlement["transact_max_dt"] > settlement["settle_due_dt"]:
                    raise ValidationError(f"Maximum transaction date must be before or equal to settlement due date.")
                if not is_valid_json(settlement["extended_data"]):
                    raise ValidationError(f"Invalid JSON for 'extended_data'.")

        except ValidationError as e:
            error_message = f"Validation error: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e