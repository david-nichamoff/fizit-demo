import logging
import json
from decimal import Decimal

from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.core.cache import cache

from api.web3 import Web3Manager
from api.config import ConfigManager
from api.cache import CacheManager
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning
from api.utilities.validation import is_valid_amount, is_valid_percentage, is_valid_json
from api.interfaces.encryption_api import get_encryptor, get_decryptor

class BaseContractAPI(ResponseMixin):
    _instances = {}

    def __new__(cls, *args, **kwargs):
        """Ensure that each subclass remains a singleton."""
        if cls not in cls._instances:
            cls._instances[cls] = super(BaseContractAPI, cls).__new__(cls)
        return cls._instances[cls]

    def __init__(self, registry_manager=None):
        """Initialize ContractAPI with necessary dependencies."""
        if not hasattr(self, "initialized"):
            self.config_manager = ConfigManager()
            self.w3_manager = Web3Manager()
            self.cache_manager = CacheManager()
            self.wallet_addr = self.config_manager.get_wallet_address("Transactor")
            self.logger = logging.getLogger(__name__)
            self.initialized = True

    def get_contract_count(self, contract_type):
        """Retrieve the total number of contracts from cache or Web3."""
        try:
            cache_key = self.cache_manager.get_contract_count_cache_key(contract_type)
            cached_count = cache.get(cache_key)

            if cached_count is not None:
                log_info(self.logger, f"Loaded contract count for {contract_type} from cache: {cached_count}")
                return self._format_success({"count": cached_count}, f"Retrieved count of contracts for {contract_type} (cached)", status.HTTP_200_OK)

            # Fetch from blockchain if not in cache
            w3_contract = self.w3_manager.get_web3_contract(contract_type)
            log_warning(self.logger, "Getting count from chain")
            count = w3_contract.functions.getContractCount().call()

            cache.set(cache_key, count, timeout=None)
            log_info(self.logger, f"Cached contract count for {contract_type}: {count}")

            return self._format_success({"count": count}, f"Retrieved count of contracts for {contract_type}", status.HTTP_200_OK)

        except Exception as e:
            return self._format_error(f"Error retrieving contract count: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_contract(self, contract_type, contract_idx, api_key=None, parties=[]):
        """Retrieve a specific contract."""
        try:
            cache_key = self.cache_manager.get_contract_cache_key(contract_type, contract_idx)
            cached_contract = cache.get(cache_key)
            decryptor = get_decryptor(api_key, parties)

            if cached_contract:
                log_info(self.logger, f"Loaded contract {contract_type}:{contract_idx} from cache")
                parsed_contract = self._decrypt_fields(contract_idx, cached_contract, decryptor)
                return self._format_success(parsed_contract, f"Retrieved {contract_type}:{contract_idx} (cached)", status.HTTP_200_OK)

            log_info(self.logger, f"Retrieving contract {contract_type}:{contract_idx} for parties {parties}")
            w3_contract = self.w3_manager.get_web3_contract(contract_type)
            raw_contract = w3_contract.functions.getContract(contract_idx).call()

            # Store contract data in Redis cache
            cache.set(cache_key, raw_contract, timeout=None)
            log_warning(self.logger, f"Cached contract {contract_type}:{contract_idx} in Redis")

            parsed_contract = self._decrypt_fields(contract_idx, raw_contract, decryptor)

            return self._format_success(parsed_contract, f"Retrieved {contract_type}:{contract_idx}", status.HTTP_200_OK)
        except ValidationError as e:
            return self._format_error(f"Contract data error for {contract_type}:{contract_idx}: {str(e)}", status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return self._format_error(f"Unexpected error retrieving contract {contract_type}:{contract_idx}: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_contract(self, contract_type, contract_dict):
        try:
            response = self.get_contract_count(contract_type)
            if response["status"] != status.HTTP_200_OK:
                raise RuntimeError("Error retrieving count of contracts")

            contract_idx = response["data"]["count"]
            log_info(self.logger, f"Building contract {contract_dict}")
            contract = self._build_contract(contract_dict)
            log_info(self.logger, f"Built contract {contract}")

            log_info(self.logger, f"Adding {contract_type}:{contract_idx} with data {contract}")
            w3_contract = self.w3_manager.get_web3_contract(contract_type)

            transaction = w3_contract.functions.addContract(contract).build_transaction()
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_type, contract_idx, "fizit")

            if tx_receipt["status"] == 1:
                cache_key = self.cache_manager.get_contract_count_cache_key(contract_type)
                cache.delete(cache_key)
                return self._format_success({"contract_idx": contract_idx}, f"Contract {contract_type}:{contract_idx} created", status.HTTP_201_CREATED)
            else:
                raise RuntimeError("Error adding contract")

        except ValidationError as e:
            return self._format_error(f"Contract data error: {str(e)}", status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return self._format_error(f"Error adding contract: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update_contract(self, contract_type, contract_idx, contract_dict):
        try:
            contract = self._build_contract(contract_dict)
            w3_contract = self.w3_manager.get_web3_contract(contract_type)
            transaction = w3_contract.functions.updateContract(contract_idx, contract).build_transaction()
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_type, contract_idx, "fizit")
    
            if tx_receipt["status"] == 1:
                cache_key = self.cache_manager.get_contract_cache_key(contract_type, contract_idx)
                cache.delete(cache_key)
                return self._format_success({"contract_idx": contract_idx}, f"Contract {contract_type}:{contract_idx} updated", status.HTTP_200_OK)
            else:
                raise RuntimeError("Error adding contract")

        except Exception as e:
            return self._format_error(f"Error adding contract: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete_contract(self, contract_type, contract_idx):
        """Delete a contract from the blockchain."""
        try:
            w3_contract = self.w3_manager.get_web3_contract(contract_type)
            transaction = w3_contract.functions.deleteContract(contract_idx).build_transaction()
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_type, contract_idx, "fizit")

            if tx_receipt["status"] == 1:
                cache_key = self.cache_manager.get_contract_cache_key(contract_type, contract_idx)
                cache.delete(cache_key)
                return self._format_success( {"contract_idx":contract_idx}, f"Contract {contract_type}:{contract_idx} deleted", status.HTTP_204_NO_CONTENT)
            else:
                raise RuntimeError(f"Transaction failed for {contract_type}:{contract_idx}.")

        except ValidationError as e:
            return self._format_error(f"Contract data error {contract_type}:{contract_idx}: {str(e)}", status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return self._format_error(f"Error deleting {contract_type}:{contract_idx}: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)

### **Subclass for Purchase Contracts**
class PurchaseContractAPI(BaseContractAPI):
    def _decrypt_fields(self, contract_idx, raw_contract, decryptor):
        """Decrypt sensitive fields of a contract."""
        try:
            parsed_contract = self._parse_contract(contract_idx, raw_contract)
            parsed_contract["extended_data"] = decryptor.decrypt(raw_contract[0])
            parsed_contract["transact_logic"] = decryptor.decrypt(raw_contract[5])
            return parsed_contract
        except Exception as e:
            raise RuntimeError(f"Decryption failed for purchase:{contract_idx}: {str(e)}") from e

    def _parse_contract(self, contract_idx, raw_contract):
        """Parse raw contract data specific to purchase contracts."""
        return {
            "contract_type": "purchase",
            "contract_idx": contract_idx,
            "extended_data": raw_contract[0],
            "contract_name": raw_contract[1],
            "funding_instr": json.loads(raw_contract[2]),
            "service_fee_pct": f"{Decimal(raw_contract[3]) / 10000:.4f}",
            "service_fee_amt": f"{Decimal(raw_contract[4]) / 100:.2f}",
            "transact_logic": raw_contract[5],
            "notes": raw_contract[6],
            "is_active": raw_contract[7],
            "is_quote": raw_contract[8],
        }

    def _build_contract(self, contract_dict):
        """Build contract data for purchase contract."""

        encryptor = get_encryptor()
        return [
            encryptor.encrypt(contract_dict["extended_data"]),
            contract_dict["contract_name"],
            json.dumps(contract_dict["funding_instr"]),
            int(Decimal(contract_dict["service_fee_pct"]) * 10000),
            int(Decimal(contract_dict["service_fee_amt"]) * 100),
            encryptor.encrypt(contract_dict["transact_logic"]),
            contract_dict.get("notes", ""),
            contract_dict["is_active"],
            contract_dict["is_quote"],
        ]

class SaleContractAPI(BaseContractAPI):
    def _decrypt_fields(self, contract_idx, raw_contract, decryptor):
        """Decrypt sensitive fields of a contract."""
        try:
            parsed_contract = self._parse_contract(contract_idx, raw_contract)

            parsed_contract["extended_data"] = decryptor.decrypt(raw_contract[0])
            parsed_contract["transact_logic"] = decryptor.decrypt(raw_contract[7])
            return parsed_contract
        except Exception as e:
            raise RuntimeError(f"Decryption failed for purchase:{contract_idx}: {str(e)}") from e

    def _parse_contract(self, contract_idx, raw_contract):
        """Parse raw contract data specific to purchase contracts."""
        return {
            "contract_type": "sale",
            "contract_idx": contract_idx,
            "extended_data": raw_contract[0],
            "contract_name": raw_contract[1],
            "funding_instr": json.loads(raw_contract[2]),
            "deposit_instr": json.loads(raw_contract[3]),
            "service_fee_pct": f"{Decimal(raw_contract[4]) / 10000:.4f}",
            "service_fee_amt": f"{Decimal(raw_contract[5]) / 100:.2f}",
            "late_fee_pct": f"{Decimal(raw_contract[6]) / 10000:.4f}",
            "transact_logic": raw_contract[7],
            "notes": raw_contract[8],
            "is_active": raw_contract[9],
            "is_quote": raw_contract[10],
        }

    def _build_contract(self, contract_dict):
        """Build contract data for purchase contract."""

        encryptor = get_encryptor()
        return [
            encryptor.encrypt(contract_dict["extended_data"]),
            contract_dict["contract_name"],
            json.dumps(contract_dict["funding_instr"]),
            json.dumps(contract_dict["deposit_instr"]),
            int(Decimal(contract_dict["service_fee_pct"]) * 10000),
            int(Decimal(contract_dict["service_fee_amt"]) * 100),
            int(Decimal(contract_dict["late_fee_pct"]) * 10000),
            encryptor.encrypt(contract_dict["transact_logic"]),
            contract_dict.get("notes", ""),
            contract_dict["is_active"],
            contract_dict["is_quote"],
        ]


### **Subclass for Advance Contracts**
class AdvanceContractAPI(BaseContractAPI):
    def _decrypt_fields(self, contract_idx, raw_contract, decryptor):
        """Decrypt sensitive fields of a contract."""
        try:
            parsed_contract = self._parse_contract(contract_idx, raw_contract)
            parsed_contract["extended_data"] = decryptor.decrypt(raw_contract[0])
            parsed_contract["transact_logic"] = decryptor.decrypt(raw_contract[9])
            return parsed_contract
        except Exception as e:
            raise RuntimeError(f"Decryption failed for advance:{contract_idx}: {str(e)}") from e

    def _parse_contract(self, contract_idx, raw_contract):
        """Parse raw contract data specific to advance contracts."""
        return {
            "contract_type": "advance",
            "contract_idx": contract_idx,
            "extended_data": raw_contract[0],
            "contract_name": raw_contract[1],
            "funding_instr": json.loads(raw_contract[2]),
            "deposit_instr": json.loads(raw_contract[3]),
            "service_fee_pct": f"{Decimal(raw_contract[4]) / 10000:.4f}",
            "service_fee_max": f"{Decimal(raw_contract[5]) / 10000:.4f}",
            "service_fee_amt": f"{Decimal(raw_contract[6]) / 100:.2f}",
            "advance_pct": f"{Decimal(raw_contract[7]) / 10000:.4f}",
            "late_fee_pct": f"{Decimal(raw_contract[8]) / 10000:.4f}",
            "transact_logic": raw_contract[9],
            "min_threshold_amt": f"{Decimal(raw_contract[10]) / 100:.2f}",
            "max_threshold_amt": f"{Decimal(raw_contract[11]) / 100:.2f}",
            "notes": raw_contract[12],
            "is_active": raw_contract[13],
            "is_quote": raw_contract[14],
        }

    def _build_contract(self, contract_dict):
        """Build contract data for advance contract."""
        encryptor = get_encryptor()
        return [
            encryptor.encrypt(contract_dict["extended_data"]),
            contract_dict["contract_name"],
            json.dumps(contract_dict["funding_instr"]),
            json.dumps(contract_dict["deposit_instr"]),
            int(Decimal(contract_dict["service_fee_pct"]) * 10000),
            int(Decimal(contract_dict["service_fee_max"]) * 10000),
            int(Decimal(contract_dict["service_fee_amt"]) * 100),
            int(Decimal(contract_dict["advance_pct"]) * 10000),
            int(Decimal(contract_dict["late_fee_pct"]) * 10000),
            encryptor.encrypt(contract_dict["transact_logic"]),
            int(Decimal(str(contract_dict.get("min_threshold_amt", "0"))) * 100),
            int(Decimal(str(contract_dict.get("max_threshold_amt", "0"))) * 100),
            contract_dict.get("notes", ""),
            contract_dict["is_active"],
            contract_dict["is_quote"],
        ]

