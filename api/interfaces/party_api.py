import logging

from django.core.exceptions import ObjectDoesNotExist
from api.managers import Web3Manager, ConfigManager
from eth_utils import to_checksum_address

class PartyAPI:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure that the class is a singleton."""
        if not cls._instance:
            cls._instance = super(PartyAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize the PartyAPI class with Web3 and Config managers."""
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.w3_manager = Web3Manager()
        self.w3 = self.w3_manager.get_web3_instance()
        self.w3_contract = self.w3_manager.get_web3_contract()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

        self.ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

        self.wallet_addr = self.config_manager.get_nested_config_value("wallet_addr", "Transactor")
        self.checksum_wallet_addr = to_checksum_address(self.wallet_addr)

    def get_party_dict(self, party, party_idx, contract_idx):
        """Helper function to create party dict structure."""
        return {
            "party_code": party[0],
            "party_addr": party[1],
            "party_type": party[2],
            "contract_idx": contract_idx,
            "party_idx": party_idx
        }

    def get_parties(self, contract_idx):
        """Retrieve parties for a given contract."""
        try:
            parties = []
            parties_ = self.w3_contract.functions.getParties(contract_idx).call()
            for party in parties_:
                party_dict = self.get_party_dict(party, len(parties), contract_idx)
                parties.append(party_dict)
            return parties
        except Exception as e:
            self.logger.error(f"Error retrieving parties for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to retrieve parties for contract {contract_idx}") from e

    def add_parties(self, contract_idx, parties):
        """Add parties to a given contract."""
        try:
            self.validate_parties(parties)
            for party in parties:
                party_addr = self.w3.to_checksum_address(self.get_party_address(party["party_code"]))
                nonce = self.w3.eth.get_transaction_count(self.checksum_wallet_addr)

                # Build the transaction
                transaction = self.w3_contract.functions.addParty(
                    contract_idx, [party["party_code"], party_addr, party["party_type"]]
                ).build_transaction({
                    "from": self.checksum_wallet_addr,
                    "nonce": nonce
                })

                # Send the transaction
                tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")

                if tx_receipt["status"] != 1:
                    raise RuntimeError(f"Failed to add party {party['party_code']} to contract {contract_idx}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding parties to contract {contract_idx}: {str(e)}")
            raise

    def get_party_address(self, party_code):
        """Retrieve the party address based on party code from config."""
        try:
            parties = self.config.get("party_addr", [])
            for party in parties:
                if party["key"] == party_code:
                    return party["value"]
            raise ValueError(f"Party with code '{party_code}' does not exist in the config.")
        except Exception as e:
            self.logger.error(f"Error retrieving address for party code '{party_code}': {str(e)}")
            raise ValueError(f"Party with code '{party_code}' does not exist.")

    def delete_parties(self, contract_idx):
        """Delete all parties from a given contract."""
        try:
            nonce = self.w3.eth.get_transaction_count(self.checksum_wallet_addr)

            # Build the transaction
            transaction = self.w3_contract.functions.deleteParties(contract_idx).build_transaction({
                "from": self.checksum_wallet_addr,
                "nonce": nonce
            })

            # Send the transaction
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")

            if tx_receipt["status"] != 1:
                raise RuntimeError(f"Failed to delete parties for contract {contract_idx}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting parties for contract {contract_idx}: {str(e)}")
            raise

    def delete_party(self, contract_idx, party_idx):
        """Delete a specific party from a given contract."""
        try:
            nonce = self.w3.eth.get_transaction_count(self.checksum_wallet_addr)

            # Build the transaction
            transaction = self.w3_contract.functions.deleteParty(contract_idx, party_idx).build_transaction({
                "from": self.checksum_wallet_addr,
                "nonce": nonce
            })

            # Send the transaction
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")

            if tx_receipt["status"] != 1:
                raise RuntimeError(f"Failed to delete party {party_idx} from contract {contract_idx}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting party {party_idx} from contract {contract_idx}: {str(e)}")
            raise

    def validate_parties(self, parties):
        """Validate the parties before adding them to the contract."""
        try:
            party_codes = self.config.get("party_addr", [])
            for party in parties:
                # Validate party_code
                if not party.get("party_code"):
                    raise ValueError("Party code is missing or empty.")
                if not any(p["key"] == party["party_code"] for p in party_codes):
                    raise ValueError(f"Party code '{party['party_code']}' does not exist.")

                # Validate party_type
                party_types = self.config.get("party_type", [])
                if not party.get("party_type"):
                    raise ValueError("Party type is missing or empty.")
                if party["party_type"] not in party_types:
                    raise ValueError(f"Party type '{party['party_type']}' does not exist.")
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            raise ValueError(f"Validation error: {str(e)}")

    def import_parties(self, contract_idx, parties):
        try:
            for party in parties:
                party_addr = party.get("party_addr", self.ZERO_ADDRESS)
                party_code = party.get("party_code")
                party_type = party.get("party_type")

                self.logger.info(f"Importing party {party_code} to contract {contract_idx}")

                # Build the transaction
                nonce = self.w3.eth.get_transaction_count(self.checksum_wallet_addr)
                transaction = self.w3_contract.functions.importParty(
                    contract_idx, [party_code, party_addr, party_type]
                ).build_transaction({
                    "from": self.checksum_wallet_addr,
                    "nonce": nonce
                })

                # Send the transaction
                tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")

                if tx_receipt["status"] != 1:
                    raise RuntimeError(f"Failed to import party {party_code} to contract {contract_idx}")

            return True

        except Exception as e:
            self.logger.error(f"Error importing parties to contract {contract_idx}: {str(e)}")
            raise