from api.models.engage_models import EngageSrc, EngageDest

import adapter.bank.mercury
import adapter.artifact.numbers
import adapter.ticketing.engage

from .contract_api import get_contract

import packages.load_web3 as load_web3
import packages.load_config as load_config

import logging

config = load_config.load_config()

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

logger = logging.getLogger(__name__)

def get_contract_invoices(contract_idx, start_date, end_date):
    try:
        contract = get_contract(contract_idx)

        if contract["contract_type"] == "ticketing": 
            if contract["extended_data"].get("provider") == "engage":
                try:
                    engage_src = EngageSrc.objects.get(src_code=contract["extended_data"]["src_code"])
                    engage_dest = EngageDest.objects.get(dest_code=contract["extended_data"]["dest_code"])
                except EngageSrc.DoesNotExist as e:
                    logger.error(f"EngageSrc not found for src_code: {contract['extended_data']['src_code']}")
                    raise ValueError(f"Source not found for src_code: {contract['extended_data']['src_code']}") from e
                except EngageDest.DoesNotExist as e:
                    logger.error(f"EngageDest not found for dest_code: {contract['extended_data']['dest_code']}")
                    raise ValueError(f"Destination not found for dest_code: {contract['extended_data']['dest_code']}") from e

                invoices = adapter.ticketing.engage.get_invoices(contract, engage_src, engage_dest, start_date, end_date)
                return invoices
            else:
                logger.error(f"Unsupported provider: {contract['extended_data'].get('provider')}")
                raise ValueError(f"Unsupported provider: {contract['extended_data'].get('provider')}")

        logger.warning(f"No invoices retrieved for contract {contract_idx} due to unsupported contract type.")
        return []

    except Exception as e:
        logger.error(f"Error retrieving invoices for contract {contract_idx}: {str(e)}")
        raise RuntimeError(f"Failed to retrieve invoices for contract {contract_idx}") from e