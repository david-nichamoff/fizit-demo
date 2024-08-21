from api.models.engage_models import EngageSrc, EngageDest

import adapter.bank.mercury
import adapter.artifact.numbers
import adapter.ticketing.engage

from .contract_api import get_contract

import packages.load_web3 as load_web3
import packages.load_config as load_config

config = load_config.load_config()

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

def get_contract_invoices(contract_idx, start_date, end_date):
    contract = get_contract(contract_idx)
    invoices = []

    if contract["contract_type"] == "ticketing": 
        if contract["extended_data"]["provider"] == "engage":
            engage_src = EngageSrc.objects.get(src_code=contract["extended_data"]["src_code"])
            engage_dest = EngageDest.objects.get(dest_code=contract["extended_data"]["dest_code"])
            invoices = adapter.ticketing.engage.get_invoices(contract, engage_src, engage_dest, start_date, end_date)

    return invoices 