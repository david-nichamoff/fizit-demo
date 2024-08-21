from packages.check_privacy import is_user_authorized

from django.core.exceptions import ObjectDoesNotExist

import packages.load_web3 as load_web3
import packages.load_config as load_config

from api.models import PartyCode, PartyType

config = load_config.load_config()

ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

def get_party_dict(party, party_idx, contract_idx):
    party_dict = {}
    party_dict["party_code"] = party[0]
    party_dict["party_address"] = party[1]
    party_dict["party_type"] = party[2]
    party_dict["contract_idx"] = contract_idx
    party_dict["party_idx"] = party_idx
    return party_dict

def get_contract_parties(contract_idx):
    parties = []
    parties_ = w3_contract.functions.getParties(contract_idx).call() 
    for party in parties_:
        party_dict = get_party_dict(party, len(parties), contract_idx)
        parties.append(party_dict)

    return parties

def add_parties(contract_idx, parties):
    validate_parties(parties)

    for party in parties:
        party_address = get_party_address(party["party_code"])
        nonce = w3.eth.get_transaction_count(config["wallet_addr"])
        call_function = w3_contract.functions.addParty(contract_idx, [party["party_code"], party_address, party["party_type"]] ).build_transaction(
            {"from":config["wallet_addr"],"nonce":nonce,"gas":config["gas_limit"]}) 
        tx_receipt = load_web3.get_tx_receipt(call_function)
        if tx_receipt["status"] != 1: return False
    return True

def get_party_address(party_code):
    try:
        party = PartyCode.objects.get(party_code=party_code)
        return party.address
    except ObjectDoesNotExist:
        raise ValueError(f"Party with code '{party_code}' does not exist.")

def delete_parties(contract_idx):
    nonce = w3.eth.get_transaction_count(config["wallet_addr"])
    call_function = w3_contract.functions.deleteParties(contract_idx).build_transaction(
        {"from":config["wallet_addr"],"nonce":nonce,"gas":config["gas_limit"]}) 
    tx_receipt = load_web3.get_tx_receipt(call_function)
    return True if tx_receipt["status"] == 1 else False   

def delete_party(contract_idx, party_idx):
    nonce = w3.eth.get_transaction_count(config["wallet_addr"])
    call_function = w3_contract.functions.deleteParty(contract_idx, party_idx).build_transaction(
        {"from":config["wallet_addr"],"nonce":nonce,"gas":config["gas_limit"]}) 
    tx_receipt = load_web3.get_tx_receipt(call_function)
    return True if tx_receipt["status"] == 1 else False   

def validate_parties(parties):
    for party in parties:
        # Check if party_code is populated
        if not party.get("party_code"):
            raise ValueError("Party code is missing or empty.")

        # Check if party_type is populated
        if not party.get("party_type"):
            raise ValueError("Party type is missing or empty.")
        
        # Validate if party_code exists in the Party table
        try:
            PartyCode.objects.get(party_code=party["party_code"])
        except ObjectDoesNotExist:
            raise ValueError(f"Party code '{party['party_code']}' does not exist in the Party table.")

        # Validate if party_type exists in the PartyType table
        try:
            PartyType.objects.get(party_type=party["party_type"])
        except ObjectDoesNotExist:
            raise ValueError(f"Party type '{party['party_type']}' does not exist in the PartyType table.")