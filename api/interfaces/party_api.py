import logging
import time
from datetime import datetime

from rest_framework import status
from rest_framework.exceptions import ValidationError
from eth_utils import keccak, to_checksum_address

from api.managers.app_context import AppContext
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning
from api.utilities.formatting import from_timestamp

class PartyAPI(ResponseMixin):

    def __init__(self, context: AppContext):
        self.context = context
        self.config_manager = context.config_manager
        self.cache_manager = context.cache_manager
        self.domain_manager = context.domain_manager
        self.wallet_addr = self.config_manager.get_wallet_address("transactor")
        self.logger = logging.getLogger(__name__)

    def get_parties(self, contract_type, contract_idx):
        """Retrieve parties for a given contract."""
        try:
            cache_key = self.cache_manager.get_party_cache_key(contract_type, contract_idx)
            cached_parties = self.cache_manager.get(cache_key)
            success_message = f"Successfully retrieved parties for {contract_type}:{contract_idx}"

            if cached_parties is not None:
                log_info(self.logger, f"Loaded parties for {contract_type}:{contract_idx} from cache")
                return self._format_success(cached_parties, success_message, status.HTTP_200_OK)
 
            network = self.domain_manager.get_contract_network()
            web3_contract = self.context.web3_manager.get_web3_contract(contract_type, network)
            raw_parties = web3_contract.functions.getParties(contract_idx).call()

            parties = [
                self._build_party_dict(raw_party, idx, contract_type, contract_idx)
                for idx, raw_party in enumerate(raw_parties)
            ]

            self.cache_manager.set(cache_key, parties, timeout=None)
            return self._format_success(parties, f"Retrieved parties for {contract_type}:{contract_idx}", status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Party validation error for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error retrieving parties for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_party_list(self, contracts, party_code):
        """Filter contracts where the given party_code is listed as a party."""
        try:
            filtered_contracts = []
            network = self.domain_manager.get_contract_network()

            for contract in contracts:
                contract_type = contract.get("contract_type")
                contract_idx = contract.get("contract_idx")

                cache_key_parties = self.cache_manager.get_party_cache_key(contract_type, contract_idx)
                cached_parties = self.cache_manager.get(cache_key_parties)

                if cached_parties is None:
                    web3_contract = self.context.web3_manager.get_web3_contract(contract_type, network)
                    raw_parties = web3_contract.functions.getParties(contract_idx).call()
                    parties = [
                        self._build_party_dict(raw_party, idx, contract_type, contract_idx)
                        for idx, raw_party in enumerate(raw_parties)
                    ]
                    self.cache_manager.set(cache_key_parties, parties, timeout=None)
                else:
                    parties = cached_parties

                if any(p["party_code"].lower() == party_code.lower() for p in parties):
                    filtered_contracts.append(contract)

            return self._format_success(filtered_contracts, f"Retrieved filtered contracts for {party_code}", status.HTTP_200_OK)

        except Exception as e:
            error_message = f"Error filtering contracts for {party_code}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_parties(self, contract_type, contract_idx, parties):
        """Add parties to a given contract."""
        try:
            for party in parties:
                party_addr = to_checksum_address(self.config_manager.get_party_address(party["party_code"]))
                network = self.domain_manager.get_contract_network()
                web3_contract = self.context.web3_manager.get_web3_contract(contract_type, network)             
                log_info(self.logger, f"Adding party: {party["party_code"]} {party_addr} {party["party_type"]}")
                function_call = web3_contract.functions.addParty(
                    contract_idx, [party["party_code"], party_addr, party["party_type"], 0, ""]
                )
                self._send_transaction(function_call, contract_type, contract_idx, f"Failed to add party {party['party_code']}")

            # Sleep to give time for transaction to complete
            time.sleep(self.config_manager.get_network_sleep_time())

            cache_key = self.cache_manager.get_party_cache_key(contract_type, contract_idx)
            self.cache_manager.delete(cache_key)

            success_message = f"Successfully added {len(parties)} parties to {contract_type}:{contract_idx}"
            return self._format_success({"count" : len(parties)}, success_message, status.HTTP_201_CREATED)
            
        except ValidationError as e:
            error_message = f"Validation data error adding parties to {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error adding parties to contract {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def approve_party(self, contract_type, contract_idx, party_idx, approved_user):
        """Approve a specific party for a contract."""
        try:
            network = self.domain_manager.get_contract_network()
            web3_contract = self.context.web3_manager.get_web3_contract(contract_type, network)
            approved_dt = int(datetime.now().timestamp())

            function_call = web3_contract.functions.approveParty(
                contract_idx, party_idx, approved_dt, approved_user
            )

            self._send_transaction(function_call, contract_type, contract_idx,  f"Failed to approve party {party_idx} on {contract_type}:{contract_idx}")

            # Wait for transaction and clear cache
            time.sleep(self.config_manager.get_network_sleep_time())

            party_cache_key = self.cache_manager.get_party_cache_key(contract_type, contract_idx)
            self.cache_manager.delete(party_cache_key)

            return self._format_success(
                {"contract_idx": contract_idx, "party_idx": party_idx},
                f"Approved party {party_idx} on {contract_type}:{contract_idx}",
                status.HTTP_200_OK
            )

        except ValidationError as e:
            error_message = f"Validation error approving party {party_idx} for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            error_message = f"Error approving party {party_idx} for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete_parties(self, contract_type, contract_idx):
        """Delete all parties from a given contract."""
        try:
            cache_key = self.cache_manager.get_party_cache_key(contract_type, contract_idx)
            cached_parties = self.cache_manager.get(cache_key)

            if cached_parties is None:
                network = self.domain_manager.get_contract_network()
                web3_contract = self.context.web3_manager.get_web3_contract(contract_type, network)
                raw_parties = web3_contract.functions.getParties(contract_idx).call()
                cached_parties = [
                    self._build_party_dict(raw_party, idx, contract_type, contract_idx)
                    for idx, raw_party in enumerate(raw_parties)
                ]

            network = self.domain_manager.get_contract_network()
            web3_contract = self.context.web3_manager.get_web3_contract(contract_type, network)
            function_call = web3_contract.functions.deleteParties(contract_idx)
            self._send_transaction(function_call, contract_type, contract_idx, "Failed to delete parties.")

            # Sleep to give time for transaction to complete
            time.sleep(self.config_manager.get_network_sleep_time())

            cache_key = self.cache_manager.get_party_cache_key(contract_type, contract_idx)
            self.cache_manager.delete(cache_key)

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
            network = self.domain_manager.get_contract_network()
            tx_receipt = self.context.web3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_type, contract_idx, network)

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
                "approved_dt": from_timestamp(raw_party[3]),
                "approved_user": raw_party[4],
                "contract_type": contract_type, 
                "contract_idx": contract_idx,
                "party_idx": party_idx,
            }
        except Exception as e:
            error_message = f"Error building party dictionary: {str(e)}"
            extra={"operation": "_build_party_dict"}
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e