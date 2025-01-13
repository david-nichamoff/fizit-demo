import logging

from rest_framework import status
from rest_framework.exceptions import ValidationError

from django.core.exceptions import ObjectDoesNotExist
from api.managers import Web3Manager, ConfigManager
from api.interfaces import ContractAPI

from api.mixins import ValidationMixin, AdapterMixin, InterfaceResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning

class PartyAPI(ValidationMixin, InterfaceResponseMixin):
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
            self.config = self.config_manager.load_config()
            self.w3_manager = Web3Manager()
            self.w3_contract = self.w3_manager.get_web3_contract()
            self.contract_api = ContractAPI()

            self.logger = logging.getLogger(__name__)
            self.initialized = True

            self.ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
            self.wallet_addr = self.config_manager.get_nested_config_value("wallet_addr", "Transactor")

    def get_parties(self, contract_idx):
        """Retrieve parties for a given contract."""
        try:
            self._validate_contract_idx(contract_idx, self.contract_api)

            raw_parties = self.w3_contract.functions.getParties(contract_idx).call()
            parties = [
                self._build_party_dict(raw_party, idx, contract_idx)
                for idx, raw_party in enumerate(raw_parties)
            ]

            return self._format_success(parties, f"Retrieved parties for contract {contract_idx}", status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Party validation error for {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error retrieving parties for contract {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_parties(self, contract_idx, parties):
        """Add parties to a given contract."""
        try:
            self._validate_contract_idx(contract_idx, self.contract_api)
            self._validate_parties(parties)

            for party in parties:
                party_addr = self._get_party_address(party["party_code"])
                function_call = self.w3_contract.functions.addParty(
                    contract_idx, [party["party_code"], party_addr, party["party_type"]]
                )
                self._send_transaction(function_call, contract_idx, f"Failed to add party {party['party_code']}")

            success_message = f"Successfully added {len(parties)} parties to contract {contract_idx}"
            return self._format_success({"count" : len(parties)}, success_message, status.HTTP_201_CREATED)
            
        except ValidationError as e:
            error_message = f"Validation data error adding parties to {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error adding parties to contract {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete_parties(self, contract_idx):
        """Delete all parties from a given contract."""
        try:
            self._validate_contract_idx(contract_idx, self.contract_api)

            function_call = self.w3_contract.functions.deleteParties(contract_idx)
            self._send_transaction(function_call, contract_idx, "Failed to delete parties.")

            success_message = f"All parties deleted for contract {contract_idx}"
            return self._format_success({"contract_idx":contract_idx}, success_message, status.HTTP_204_NO_CONTENT)

        except ValidationError as e:
            error_message = f"Validation error for {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error deleting parties for contract {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete_party(self, contract_idx, party_idx):
        """Delete a party from a given contract."""
        try:
            self._validate_contract_idx(contract_idx, self.contract_api)

            function_call = self.w3_contract.functions.deleteParty(contract_idx, party_idx)
            self._send_transaction(function_call, contract_idx, "Failed to delete party")

            success_message = f"Party {party_idx} deleted for contract {contract_idx}"
            return self._format_success({"contract_idx":contract_idx}, success_message, status.HTTP_204_NO_CONTENT)

        except ValidationError as e:
            error_message = f"Validation error for {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error deleting parties for contract {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def import_parties(self, contract_idx, parties):
        """Import parties into a given contract."""
        try:
            self._validate_contract_idx(contract_idx, self.contract_api)

            for party in parties:
                party_addr = party.get("party_addr", self.ZERO_ADDRESS)
                function_call = self.w3_contract.functions.importParty(
                    contract_idx, [party["party_code"], party_addr, party["party_type"]]
                )
                self._send_transaction(function_call, contract_idx, f"Failed to import party {party['party_code']}")

            success_message = f"Successfully imported {len(parties)} parties into contract {contract_idx}"
            return self._format_success({"count":len(parties)}, success_message, status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Validation error importing parties for {contract_idx}: {str(e)}"
            extra={"operation": "get_contract", "contract_idx": contract_idx}
            return self._log.error(error_message, status.HTTP_400_BAD_REQUEST, extra)
        except Exception as e:
            error_message = f"Error importing parties for contract {contract_idx}: {str(e)}"
            extra={"operation": "get_contract", "contract_idx": contract_idx}
            return self._log.error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR, extra)

    def _get_party_address(self, party_code):
        """Retrieve the address for a given party code."""
        try:
            for party in self.config.get("party_addr", []):
                if party["key"] == party_code:
                    return self.w3_manager.get_checksum_address(party["value"])

            raise ValidationError

        except ValidationError as e:
            error_message = f"Validation error for {party_code}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error retrieving address for party code '{party_code}': {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _validate_parties(self, parties):
        """Validate parties before adding them to the contract."""
        valid_party_codes = {p["key"] for p in self.config.get("party_addr", [])}
        valid_party_types = set(self.config.get("party_type", []))

        for party in parties:
            if not party.get("party_code") or party["party_code"] not in valid_party_codes:
                error_message = f"Invalid or missing party code: {party['party_code']}"
                log_error(self.logger, error_message)
                raise ValidationError(error_message)
            if not party.get("party_type") or party["party_type"] not in valid_party_types:
                error_message = f"Invalid or missing party type: {party['party_type']}"
                log_error(self.logger, error_message)
                raise ValidationError(error_message)

    def _send_transaction(self, function_call, contract_idx, error_message):
        """Helper method to build and send a transaction."""
        try:
            transaction = function_call.build_transaction()
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")

            if tx_receipt["status"] != 1:
                raise RuntimeError(error_message)

        except Exception as e:
            error_message = f"Error in transaction: {str(e)}" 
            self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _build_party_dict(self, raw_party, party_idx, contract_idx):
        """Create a dictionary structure for a party."""
        try:
            return {
                "party_code": raw_party[0],
                "party_addr": raw_party[1],
                "party_type": raw_party[2],
                "contract_idx": contract_idx,
                "party_idx": party_idx,
            }
        except Exception as e:
            error_message = f"Error building party dictionary: {str(e)}"
            extra={"operation": "_build_party_dict"}
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e