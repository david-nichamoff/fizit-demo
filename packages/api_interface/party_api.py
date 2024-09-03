from django.core.exceptions import ObjectDoesNotExist
import logging

import packages.load_web3 as load_web3
import packages.load_config as load_config

from api.models import PartyCode, PartyType

config = load_config.load_config()

ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

logger = logging.getLogger(__name__)

def get_party_dict(party, party_idx, contract_idx):
    return {
        "party_code": party[0],
        "party_address": party[1],
        "party_type": party[2],
        "contract_idx": contract_idx,
        "party_idx": party_idx
    }

def get_parties(contract_idx):
    try:
        parties = []
        parties_ = w3_contract.functions.getParties(contract_idx).call()
        for party in parties_:
            party_dict = get_party_dict(party, len(parties), contract_idx)
            parties.append(party_dict)
        return parties
    except Exception as e:
        logger.error(f"Error retrieving parties for contract {contract_idx}: {str(e)}")
        raise RuntimeError(f"Failed to retrieve parties for contract {contract_idx}") from e

def add_parties(contract_idx, parties):
    try:
        validate_parties(parties)
        for party in parties:
            party_address = get_party_address(party["party_code"])
            nonce = w3.eth.get_transaction_count(config["wallet_addr"])
            call_function = w3_contract.functions.addParty(
                contract_idx, [party["party_code"], party_address, party["party_type"]]
            ).build_transaction({
                "from": config["wallet_addr"],
                "nonce": nonce,
                "gas": config["gas_limit"]
            })
            tx_receipt = load_web3.get_tx_receipt(call_function)
            if tx_receipt["status"] != 1:
                raise RuntimeError(f"Failed to add party {party['party_code']} to contract {contract_idx}")
        return True
    except Exception as e:
        logger.error(f"Error adding parties to contract {contract_idx}: {str(e)}")
        raise

def get_party_address(party_code):
    try:
        party = PartyCode.objects.get(party_code=party_code)
        return party.address
    except ObjectDoesNotExist:
        logger.error(f"Party with code '{party_code}' does not exist.")
        raise ValueError(f"Party with code '{party_code}' does not exist.")

def delete_parties(contract_idx):
    try:
        nonce = w3.eth.get_transaction_count(config["wallet_addr"])
        call_function = w3_contract.functions.deleteParties(contract_idx).build_transaction({
            "from": config["wallet_addr"],
            "nonce": nonce,
            "gas": config["gas_limit"]
        })
        tx_receipt = load_web3.get_tx_receipt(call_function)
        if tx_receipt["status"] != 1:
            raise RuntimeError(f"Failed to delete parties for contract {contract_idx}")
        return True
    except Exception as e:
        logger.error(f"Error deleting parties for contract {contract_idx}: {str(e)}")
        raise

def delete_party(contract_idx, party_idx):
    try:
        nonce = w3.eth.get_transaction_count(config["wallet_addr"])
        call_function = w3_contract.functions.deleteParty(contract_idx, party_idx).build_transaction({
            "from": config["wallet_addr"],
            "nonce": nonce,
            "gas": config["gas_limit"]
        })
        tx_receipt = load_web3.get_tx_receipt(call_function)
        if tx_receipt["status"] != 1:
            raise RuntimeError(f"Failed to delete party {party_idx} from contract {contract_idx}")
        return True
    except Exception as e:
        logger.error(f"Error deleting party {party_idx} from contract {contract_idx}: {str(e)}")
        raise

def validate_parties(parties):
    for party in parties:
        try:
            # Validate party_code
            if not party.get("party_code"):
                raise ValueError("Party code is missing or empty.")
            PartyCode.objects.get(party_code=party["party_code"])

            # Validate party_type
            if not party.get("party_type"):
                raise ValueError("Party type is missing or empty.")
            PartyType.objects.get(party_type=party["party_type"])

        except ObjectDoesNotExist as e:
            logger.error(f"Validation error: {str(e)}")
            raise ValueError(f"Validation error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during party validation: {str(e)}")
            raise