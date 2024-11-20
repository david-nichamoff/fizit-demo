import logging
import json
from decimal import Decimal
from web3.exceptions import ContractLogicError, BadFunctionCallOutput
from eth_utils import to_checksum_address

from api.managers import Web3Manager, ConfigManager
from api.interfaces.encryption_api import get_encryptor, get_decryptor

from .util_api import is_valid_json

class ContractAPI:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure the class is a singleton."""
        if not cls._instance:
            cls._instance = super(ContractAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.w3_manager = Web3Manager()
        self.w3_contract = self.w3_manager.get_web3_contract()

        self.logger = logging.getLogger(__name__)
        self.initialized = True 

        self.wallet_addr = self.config_manager.get_nested_config_value("wallet_addr", "Transactor")
        self.checksum_wallet_addr = to_checksum_address(self.wallet_addr)

    def get_contract_count(self):
        try:
            contract_count = self.w3_contract.functions.getContractCount().call() 
            self.logger.info(f"Contract count: {contract_count}")
            return contract_count
        except Exception as e:
            self.logger.error(f"Error retrieving contract count: {str(e)}")
            raise RuntimeError("Failed to retrieve contract count") from e

    def get_contract_dict(self, contract_idx, api_key, parties):
        # Fetch the AES key for decryption
        decryptor = get_decryptor(api_key, parties)
        self.logger.info(f"Decrypting contract data for contract {contract_idx}")
        contract_dict = {}

        try:
            contract = self.w3_contract.functions.getContract(contract_idx).call()
        except ContractLogicError as e:
            self.logger.error(f"Contract logic error when retrieving contract {contract_idx}: {str(e)}")
            raise
        except BadFunctionCallOutput as e:
            self.logger.error(f"Bad function call output when retrieving contract {contract_idx}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error when retrieving contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to retrieve contract {contract_idx}") from e

        try:
            # Decrypt sensitive fields after retrieving from blockchain
            decrypted_extended_data = decryptor.decrypt(contract[0])
            decrypted_transact_logic = decryptor.decrypt(contract[9])

            # Convert decrypted strings back into JSON objects
            contract_dict["extended_data"] = decrypted_extended_data
            contract_dict["contract_name"] = contract[1]
            contract_dict["contract_type"] = contract[2]
            contract_dict["funding_instr"] = json.loads(contract[3])
            contract_dict["service_fee_pct"] = f'{Decimal(contract[4]) / 10000:.4f}'
            contract_dict["service_fee_max"] = f'{Decimal(contract[5]) / 10000:.4f}'
            contract_dict["service_fee_amt"] = f'{Decimal(contract[6]) / 100:.2f}'
            contract_dict["advance_pct"] = f'{Decimal(contract[7]) / 10000:.4f}'
            contract_dict["late_fee_pct"] = f'{Decimal(contract[8]) / 10000:.4f}'
            contract_dict["transact_logic"] = decrypted_transact_logic
            contract_dict["min_threshold"] = f'{Decimal(contract[10]) / 100:.2f}'
            contract_dict["max_threshold"] = f'{Decimal(contract[11]) / 100:.2f}'
            contract_dict["notes"] = contract[12]
            contract_dict["is_active"] = contract[13]
            contract_dict["is_quote"] = contract[14]
            contract_dict["contract_idx"] = contract_idx
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decoding error for contract {contract_idx}: {str(e)}")
            raise ValueError(f"Invalid JSON structure in contract {contract_idx}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error processing contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to process contract {contract_idx}") from e

        return contract_dict

    def get_contracts(self):
        contracts = []
        try:
            contract_count = self.get_contract_count()
        except Exception as e:
            self.logger.error(f"Error retrieving contract count: {str(e)}")
            raise RuntimeError("Failed to retrieve contract count") from e

        for contract_idx in range(contract_count):
            try:
                contract_dict = self.get_contract_dict(contract_idx, None, [])
                contracts.append(contract_dict)
            except Exception as e:
                self.logger.error(f"Error processing contract {contract_idx}: {str(e)}")
                raise RuntimeError(f"Failed to process contract {contract_idx}") from e

        return contracts

    def get_contract(self, contract_idx, api_key=None, parties=[]):
        try:
            self.logger.info(f"Retrieving contract {contract_idx}")
            return self.get_contract_dict(contract_idx, api_key, parties)
        except Exception as e:
            self.logger.error(f"Error retrieving contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to retrieve contract {contract_idx}") from e

    def build_contract(self, contract_dict, contract_idx):
        # Validate contract data
        self.validate_contract_data(contract_dict)

        # Fetch the AES key for encryption
        encryptor = get_encryptor()
        self.logger.info(f"Using encryption API for contract {contract_idx}")

        # Encrypt sensitive fields before sending to blockchain
        encrypted_extended_data = encryptor.encrypt(contract_dict["extended_data"])
        encrypted_transact_logic = encryptor.encrypt(contract_dict["transact_logic"])

        contract = []
        contract.append(encrypted_extended_data)  # Encrypt extended_data
        contract.append(contract_dict["contract_name"])
        contract.append(contract_dict["contract_type"])
        contract.append(json.dumps(contract_dict["funding_instr"]))
        contract.append(int(Decimal(contract_dict["service_fee_pct"]) * 10000))
        contract.append(int(Decimal(contract_dict["service_fee_max"]) * 10000))
        contract.append(int(Decimal(contract_dict["service_fee_amt"]) * 100))
        contract.append(int(Decimal(contract_dict["advance_pct"]) * 10000))
        contract.append(int(Decimal(contract_dict["late_fee_pct"]) * 10000))
        contract.append(encrypted_transact_logic)  # Encrypt transact_logic
        contract.append(int(Decimal(contract_dict["min_threshold"]) * 100))
        contract.append(int(Decimal(contract_dict["max_threshold"]) * 100))
        contract.append(contract_dict["notes"])
        contract.append(contract_dict["is_active"])
        contract.append(contract_dict["is_quote"])

        return contract

    def update_contract(self, contract_idx, contract_dict):
        try:
            self.logger.info(f"Updating contract: {contract_idx}")
            contract = self.build_contract(contract_dict, contract_idx)
            nonce = self.w3_manager.get_nonce(self.checksum_wallet_addr)

            transaction = self.w3_contract.functions.updateContract(contract_idx, contract).build_transaction({
                "from": self.checksum_wallet_addr,
                "nonce": nonce
            })

            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr)

            if tx_receipt["status"] != 1:
                self.logger.error(f"Transaction failed for contract {contract_idx}. Receipt: {tx_receipt}")
                raise RuntimeError(f"Failed to update contract {contract_idx}. Transaction status: {tx_receipt['status']}")
        except Exception as e:
            self.logger.error(f"Error updating contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to update contract {contract_idx}") from e

    def add_contract(self, contract_dict):
        try:
            contract_idx = self.get_contract_count()
            self.logger.info(f"Adding contract: {contract_idx}")
            contract = self.build_contract(contract_dict, contract_idx)
            nonce = self.w3_manager.get_nonce(self.checksum_wallet_addr)

            transaction = self.w3_contract.functions.addContract(contract).build_transaction({
                "from": self.checksum_wallet_addr,
                "nonce": nonce
            })

            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr)

            if tx_receipt["status"] == 1:
                return contract_idx
            else:
                self.logger.error(f"Transaction failed for contract {contract_idx}. Receipt: {tx_receipt}")
                raise RuntimeError(f"Failed to add contract {contract_idx}. Transaction status: {tx_receipt['status']}")
        except Exception as e:
            self.logger.error(f"An error occurred while adding contract: {e}")
            raise RuntimeError("Failed to add contract") from e

    def delete_contract(self, contract_idx):
        try:
            self.logger.info(f"Deleting contract: {contract_idx}")
            nonce = self.w3_manager.get_nonce(self.checksum_wallet_addr)

            transaction = self.w3_contract.functions.deleteContract(contract_idx).build_transaction({
                "from": self.checksum_wallet_addr,
                "nonce": nonce
            })

            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr)

            if tx_receipt["status"] != 1:
                self.logger.error(f"Transaction failed for contract {contract_idx}. Receipt: {tx_receipt}")
                raise RuntimeError(f"Failed to delete contract {contract_idx}. Transaction status: {tx_receipt['status']}")
        except Exception as e:
            self.logger.error(f"Error deleting contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to delete contract {contract_idx}") from e

    def import_contract(self, contract_dict):
        try:
            contract_idx = self.get_contract_count()
            self.logger.info(f"Importing contract: {contract_idx}")
            contract = self.build_contract(contract_dict, contract_idx)
            nonce = self.w3_manager.get_nonce(self.checksum_wallet_addr)

            transaction = self.w3_contract.functions.importContract(contract).build_transaction({
                "from": self.checksum_wallet_addr,
                "nonce": nonce
            })

            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr)

            if tx_receipt["status"] == 1:
                self.logger.info(f"Successfully imported contract: {contract_idx}")
                return contract_idx
            else:
                self.logger.error(f"Transaction failed for importing contract {contract_idx}. Receipt: {tx_receipt}")
                raise RuntimeError(f"Failed to import contract {contract_idx}. Transaction status: {tx_receipt['status']}")
        except Exception as e:
            self.logger.error(f"Error importing contract: {str(e)}")
            raise RuntimeError("Failed to import contract") from e

    def validate_contract_data(self, contract_dict):
        # Retrieve contract types from config
        valid_contract_types = self.config_manager.get_config_value("contract_type")
        
        # Check if the provided contract type is valid
        if contract_dict["contract_type"] not in valid_contract_types:
            raise ValueError(
                f"Invalid contract type: '{contract_dict['contract_type']}'. "
                f"Valid types are: {', '.join(valid_contract_types)}."
            )

        # Check if the funding_instr.bank is valid
        if contract_dict["funding_instr"]["bank"] not in ['mercury', 'token']:
            raise ValueError(f"Invalid bank: '{contract_dict['funding_instr']['bank']}'. Valid banks are: 'mercury'.")

        # Check if the percentage fields are valid
        for field in ["service_fee_pct", "service_fee_max", "advance_pct", "late_fee_pct"]:
            if not isinstance(contract_dict[field], str) or not ContractAPI.validate_percentage(contract_dict[field]):
                raise ValueError(f"Invalid value for '{field}': '{contract_dict[field]}'. Must be a string in the form X.XXXX and between 0.0000 and 1.0000.")

        # Check if the amount fields are valid
        for field in ["service_fee_amt", "max_threshold"]:
            if not isinstance(contract_dict[field], str) or not ContractAPI.validate_amount(contract_dict[field]):
                raise ValueError(f"Invalid value for '{field}': '{contract_dict[field]}'. Must be a string in the form Y.XX where Y >= 0.")

        # Check if min_threshold is valid
        if not isinstance(contract_dict["min_threshold"], str) or not ContractAPI.validate_amount(contract_dict["min_threshold"], allow_negative=True):
            raise ValueError(f"Invalid value for 'min_threshold': '{contract_dict['min_threshold']}.' Must be a string in the form Y.XX where Y can be any number (including negative).")

        # Check if transact_logic, extended_data, and transact_logic are valid JSON
        for field in ["transact_logic", "extended_data"]:
            if not is_valid_json(contract_dict[field]):
                raise ValueError(f"Invalid JSON for '{field}': '{contract_dict[field]}'.")

        # Check if is_active and is_quote are booleans
        for field in ["is_active", "is_quote"]:
            if not isinstance(contract_dict[field], bool):
                raise ValueError(f"Invalid value for '{field}': '{contract_dict[field]}'. Must be true or false.")

        # Check that min_threshold <= max_threshold
        if Decimal(contract_dict["min_threshold"]) > Decimal(contract_dict["max_threshold"]):
            raise ValueError(f"'min_threshold' ({contract_dict['min_threshold']}) must be less than or equal to 'max_threshold' ({contract_dict['max_threshold']}).")

        # Check that service_fee_max >= service_fee_pct
        if Decimal(contract_dict["service_fee_max"]) < Decimal(contract_dict["service_fee_pct"]):
            raise ValueError(f"'service_fee_max' ({contract_dict['service_fee_max']}) must be greater than or equal to 'service_fee_pct' ({contract_dict['service_fee_pct']}).")

        # Check if contract_name and notes are valid strings
        for field in ["contract_name", "notes"]:
            if not isinstance(contract_dict[field], str) or not contract_dict[field].strip():
                raise ValueError(f"Invalid value for '{field}': '{contract_dict[field]}'. Must be a non-empty string.")

    @staticmethod
    def validate_percentage(value):
        try:
            decimal_value = Decimal(value)
            return 0 <= decimal_value <= 1 and len(value.split('.')[1]) == 4
        except (ValueError, IndexError):
            return False

    @staticmethod
    def validate_amount(value, allow_negative=False):
        try:
            decimal_value = Decimal(value)
            if not allow_negative and decimal_value < 0:
                return False
            return len(value.split('.')[1]) == 2
        except (ValueError, IndexError):
            return False