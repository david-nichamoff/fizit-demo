import logging

from rest_framework import status
from rest_framework.exceptions import ValidationError
from eth_utils import keccak, to_checksum_address
from django.core.cache import cache

from api.web3 import Web3Manager
from api.config import ConfigManager
from api.cache import CacheManager
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning

class PartyAPI(ResponseMixin):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure that the class is a singleton."""
        if not cls._instance:
            cls._instance = super(PartyAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize the PartyAPI class with Web3 and Config managers."""
        if not hasattr(self, "initialized"):
            self.config_manager = ConfigManager()
            self.w3_manager = Web3Manager()
            self.cache_manager = CacheManager()
            self.logger = logging.getLogger(__name__)
            self.initialized = True

            self.ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
            self.wallet_addr = self.config_manager.get_wallet_address("Transactor")

    def get_parties(self, contract_type, contract_idx):
        """Retrieve parties for a given contract."""
        try:
            cache_key = self.cache_manager.get_party_cache_key(contract_type, contract_idx)
            cached_parties = cache.get(cache_key)
            success_message = f"Successfully retrieved parties for {contract_type}:{contract_idx}"

            if cached_parties is not None:
                log_info(self.logger, f"Loaded parties for {contract_type}:{contract_idx} from cache")
                return self._format_success(cached_parties, success_message, status.HTTP_200_OK)
 
            w3_contract = self.w3_manager.get_web3_contract(contract_type)
            raw_parties = w3_contract.functions.getParties(contract_idx).call()
            log_warning(self.logger, f"Retrieved settlements {raw_parties} for {contract_type}:{contract_idx} from chain")

            parties = [
                self._build_party_dict(raw_party, idx, contract_type, contract_idx)
                for idx, raw_party in enumerate(raw_parties)
            ]

            cache.set(cache_key, parties, timeout=None)
            return self._format_success(parties, f"Retrieved parties for {contract_type}:{contract_idx}", status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Party validation error for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error retrieving parties for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_parties(self, contract_type, contract_idx, parties):
        """Add parties to a given contract."""
        try:
            for party in parties:
                party_addr = to_checksum_address(self.config_manager.get_party_address(party["party_code"]))
                w3_contract = self.w3_manager.get_web3_contract(contract_type)               
                log_info(self.logger, f"Adding party: {party["party_code"]} {party_addr} {party["party_type"]}")
                function_call = w3_contract.functions.addParty(
                    contract_idx, [party["party_code"], party_addr, party["party_type"]]
                )
                self._send_transaction(function_call, contract_type, contract_idx, f"Failed to add party {party['party_code']}")

            cache_key = self.cache_manager.get_party_cache_key(contract_type, contract_idx)
            cache.delete(cache_key)

            success_message = f"Successfully added {len(parties)} parties to {contract_type}:{contract_idx}"
            return self._format_success({"count" : len(parties)}, success_message, status.HTTP_201_CREATED)
            
        except ValidationError as e:
            error_message = f"Validation data error adding parties to {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error adding parties to contract {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete_parties(self, contract_type, contract_idx):
        """Delete all parties from a given contract."""
        try:
            w3_contract = self.w3_manager.get_web3_contract(contract_type)      
            function_call = w3_contract.functions.deleteParties(contract_idx)
            self._send_transaction(function_call, contract_type, contract_idx, "Failed to delete parties.")

            cache_key = self.cache_manager.get_party_cache_key(contract_type, contract_idx)
            cache.delete(cache_key)

            success_message = f"All parties deleted for {contract_type}:{contract_idx}"
            return self._format_success({"contract_idx":contract_idx}, success_message, status.HTTP_204_NO_CONTENT)

        except ValidationError as e:
            error_message = f"Validation error for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error deleting parties for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _send_transaction(self, function_call, contract_type, contract_idx, error_message):
        """Helper method to build and send a transaction."""
        try:
            transaction = function_call.build_transaction()
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_type, contract_idx, "fizit")

            if tx_receipt["status"] != 1:
                raise RuntimeError(error_message)

        except Exception as e:
            error_message = f"Error in transaction: {str(e)}" 
            self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _build_party_dict(self, raw_party, party_idx, contract_type, contract_idx):
        """Create a dictionary structure for a party."""
        try:
            return {
                "party_code": raw_party[0],
                "party_addr": raw_party[1],
                "party_type": raw_party[2],
                "contract_type": contract_type, 
                "contract_idx": contract_idx,
                "party_idx": party_idx,
            }
        except Exception as e:
            error_message = f"Error building party dictionary: {str(e)}"
            extra={"operation": "_build_party_dict"}
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e