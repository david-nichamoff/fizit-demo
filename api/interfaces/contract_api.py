import logging
import json
from decimal import Decimal

from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.managers import Web3Manager, ConfigManager
from api.interfaces.encryption_api import get_encryptor, get_decryptor

from api.mixins import ValidationMixin, AdapterMixin, InterfaceResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning
from api.utilities.validation import is_valid_amount, is_valid_percentage, is_valid_json

class ContractAPI(ValidationMixin, InterfaceResponseMixin):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure the class is a singleton."""
        if not cls._instance:
            cls._instance = super(ContractAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize ContractAPI with necessary dependencies."""
        if not hasattr(self, "initialized"):
            self.config_manager = ConfigManager()
            self.config = self.config_manager.load_config()
            self.w3_manager = Web3Manager()
            self.w3_contract = self.w3_manager.get_web3_contract()
            self.wallet_addr = self.config_manager.get_nested_config_value("wallet_addr", "Transactor")
            self.logger = logging.getLogger(__name__)
            self.initialized = True

    def get_contract_count(self):
        """Retrieve the total number of contracts."""
        try:
            count = self.w3_contract.functions.getContractCount().call()
            return self._format_success({"count": count}, "Retrieved count of contracts", status.HTTP_200_OK)

        except Exception as e:
            error_message = f"Error retrieving contract count: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_contract(self, contract_idx, api_key=None, parties=[]):
        """Retrieve a specific contract."""
        try:
            # Validate contract_idx
            self._validate_contract_idx(contract_idx, self)
            
            decryptor = get_decryptor(api_key, parties)
            raw_contract = self.w3_contract.functions.getContract(contract_idx).call()
            parsed_contract = self._decrypt_fields(contract_idx, raw_contract, decryptor)

            return self._format_success(parsed_contract, f"Retrieved contract {contract_idx}", status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Contract data error for {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Unexpected error retrieving contract {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_contract(self, contract_dict):
        """Add a new contract to the blockchain."""
        try:
            response = self.get_contract_count()
            if response["status"] != status.HTTP_200_OK:
                raise RuntimeError("Error retrieving count of contracts")

            contract_idx = response["data"]["count"]
            log_info(self.logger, f"Adding contract {contract_idx}")

            contract = self._build_contract(contract_dict)
            log_info(self.logger, f"Adding contract data {contract}")

            transaction = self.w3_contract.functions.addContract(contract).build_transaction()
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")

            if tx_receipt["status"] == 1:
                success_message = f"Contract {contract_idx} created"
                return self._format_success({"contract_idx": contract_idx}, success_message, status.HTTP_201_CREATED)
            else:
                raise RuntimeError("Error adding contract")

        except ValidationError as e:
            error_message = f"Contract data error: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error adding contract: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update_contract(self, contract_idx, contract_dict):
        try:
            contract = self._build_contract(contract_dict)
            transaction = self.w3_contract.functions.updateContract(contract_idx, contract).build_transaction()
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")
    
            if tx_receipt["status"] == 1:
                success_message = f"Contract {contract_idx} updated"
                return self._format_success({"contract_idx": contract_idx}, success_message, status.HTTP_200_OK)
            else:
                raise RuntimeError("Error adding contract")

        except Exception as e:
            error_message = f"Error adding contract: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete_contract(self, contract_idx):
        """Delete a contract from the blockchain."""
        try:
            # Validate contract_idx
            self._validate_contract_idx(contract_idx, self)

            transaction = self.w3_contract.functions.deleteContract(contract_idx).build_transaction()
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")

            if tx_receipt["status"] == 1:
                data = { "contract_idx" : contract_idx }
                return self._format_success(data, f"Contract {contract_idx} deleted", status.HTTP_204_NO_CONTENT)
            else:
                error_message = f"Transaction failed for contract {contract_idx}."
                log_error(self.logger, error_message)
                raise RuntimeError(error_message)

        except ValidationError as e:
            error_message = f"Contract data error for {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error deleting contract {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _decrypt_fields(self, contract_idx, raw_contract, decryptor):
        """Decrypt sensitive fields of a contract."""
        try:
            decrypted_extended_data = decryptor.decrypt(raw_contract[0])
            decrypted_transact_logic = decryptor.decrypt(raw_contract[10])
        
            parsed_contract = self._parse_contract(contract_idx, raw_contract)
            parsed_contract["extended_data"] = decrypted_extended_data
            parsed_contract["transact_logic"] = decrypted_transact_logic

            return parsed_contract

        except Exception as e:
            error_message = f"Decryption failed for contract {contract_idx}: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _parse_contract(self, contract_idx, raw_contract):
        """
        Parse raw contract data from the blockchain into a structured dictionary.
        """
        try:
            return {
                "contract_idx": contract_idx,
                "extended_data": raw_contract[0],
                "contract_name": raw_contract[1],
                "contract_type": raw_contract[2],
                "funding_instr": json.loads(raw_contract[3]),
                "deposit_instr": json.loads(raw_contract[4]),
                "service_fee_pct": f"{Decimal(raw_contract[5]) / 10000:.4f}",
                "service_fee_max": f"{Decimal(raw_contract[6]) / 10000:.4f}",
                "service_fee_amt": f"{Decimal(raw_contract[7]) / 100:.2f}",
                "advance_pct": f"{Decimal(raw_contract[8]) / 10000:.4f}",
                "late_fee_pct": f"{Decimal(raw_contract[9]) / 10000:.4f}",
                "transact_logic": raw_contract[10],
                "min_threshold_amt": f"{Decimal(raw_contract[11]) / 100:.2f}",
                "max_threshold_amt": f"{Decimal(raw_contract[12]) / 100:.2f}",
                "notes": raw_contract[13],
                "is_active": raw_contract[14],
                "is_quote": raw_contract[15],
            }

        except (IndexError, ValueError, json.JSONDecodeError) as e:
            error_message = f"Error parsing raw contract data: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _build_contract(self, contract_dict):
        """Build a contract for submission to the blockchain."""
        try:
            self._validate_contract_data(contract_dict)  # Validate the contract data
            encryptor = get_encryptor()

            encrypted_extended_data = encryptor.encrypt(contract_dict["extended_data"])
            encrypted_transact_logic = encryptor.encrypt(contract_dict["transact_logic"])

            contract = [
                encrypted_extended_data,
                contract_dict["contract_name"],
                contract_dict["contract_type"],
                json.dumps(contract_dict["funding_instr"]),
                json.dumps(contract_dict["deposit_instr"]),
                int(Decimal(contract_dict["service_fee_pct"]) * 10000),
                int(Decimal(contract_dict["service_fee_max"]) * 10000),
                int(Decimal(contract_dict["service_fee_amt"]) * 100),
                int(Decimal(contract_dict["advance_pct"]) * 10000),
                int(Decimal(contract_dict["late_fee_pct"]) * 10000),
                encrypted_transact_logic,
                int(Decimal(contract_dict["min_threshold_amt"]) * 100),
                int(Decimal(contract_dict["max_threshold_amt"]) * 100),
                contract_dict["notes"],
                contract_dict["is_active"],
                contract_dict["is_quote"],
            ]

            return contract

        except ValidationError as e:
            error_message = f"Validation error building contract: {str(e)}"
            log_error(self.logger, error_message)
            raise ValidationError(error_message) from e
        except Exception as e:
            error_message = f"Error building contract: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _validate_contract_data(self, contract_dict):
        """Validate the data in the contract."""
        try:

            # Check if the provided contract type is valid
            valid_contract_types = self.config_manager.get_config_value("contract_type")
            if contract_dict["contract_type"] not in valid_contract_types:
                raise ValidationError(
                    f"Invalid contract type: '{contract_dict['contract_type']}'. "
                    f"Valid types are: {', '.join(valid_contract_types)}."
                )

            # Check if the funding_instr.bank is valid
            if contract_dict["funding_instr"]["bank"] not in ['mercury', 'token']:
                raise ValidationError(f"Invalid bank: '{contract_dict['funding_instr']['bank']}'. Valid banks are: 'mercury', 'token'.")

            # Check if the deposit_instr.bank is valid
            if contract_dict["deposit_instr"]["bank"] not in ['mercury', 'token']:
                raise ValidationError(f"Invalid bank: '{contract_dict['deposit_instr']['bank']}'. Valid banks are: 'mercury', 'token'.")

            # Check if the percentage fields are valid
            for field in ["service_fee_pct", "service_fee_max", "advance_pct", "late_fee_pct"]:
                if not isinstance(contract_dict[field], str) or not is_valid_percentage(contract_dict[field]):
                    raise ValidationError(f"Invalid value for '{field}': '{contract_dict[field]}'. Must be a string in the form X.XXXX and between 0.0000 and 1.0000.")

            # Check if the amount fields are valid
            for field in ["service_fee_amt", "max_threshold_amt"]:
                if not isinstance(contract_dict[field], str) or not is_valid_amount(contract_dict[field]):
                    raise ValidationError(f"Invalid value for '{field}': '{contract_dict[field]}'. Must be a string in the form Y.XX where Y >= 0.")

            # Check if min_threshold_amt is valid
            if not isinstance(contract_dict["min_threshold_amt"], str) or not is_valid_amount(contract_dict["min_threshold_amt"], allow_negative=True):
                raise ValidationError(f"Invalid value for 'min_threshold_amt': '{contract_dict['min_threshold_amt']}.' Must be a string in the form Y.XX where Y can be any number (including negative).")

            # Check if transact_logic, extended_data, and transact_logic are valid JSON
            for field in ["transact_logic", "extended_data"]:
                if not is_valid_json(contract_dict[field]):
                    raise ValidationError(f"Invalid JSON for '{field}': '{contract_dict[field]}'.")

            # Check if is_active and is_quote are booleans
            for field in ["is_active", "is_quote"]:
                if not isinstance(contract_dict[field], bool):
                    raise ValidationError(f"Invalid value for '{field}': '{contract_dict[field]}'. Must be true or false.")

            # Check that min_threshold_amt <= max_threshold_amt
            if Decimal(contract_dict["min_threshold_amt"]) > Decimal(contract_dict["max_threshold_amt"]):
                raise ValidationError(f"'min_threshold_amt' ({contract_dict['min_threshold_amt']}) must be less than or equal to 'max_threshold_amt' ({contract_dict['max_threshold_amt']}).")

            # Check that service_fee_max >= service_fee_pct
            if Decimal(contract_dict["service_fee_max"]) < Decimal(contract_dict["service_fee_pct"]):
                raise ValidationError(f"'service_fee_max' ({contract_dict['service_fee_max']}) must be greater than or equal to 'service_fee_pct' ({contract_dict['service_fee_pct']}).")

            # Check if contract_name and notes are valid strings
            for field in ["contract_name", "notes"]:
                if not isinstance(contract_dict[field], str) or not contract_dict[field].strip():
                    raise ValidationError(f"Invalid value for '{field}': '{contract_dict[field]}'. Must be a non-empty string.")

        except Exception as e:
            error_message = f"Runtime validation error: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e
