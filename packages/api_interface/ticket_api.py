from django.core.exceptions import ObjectDoesNotExist
from api.models.engage_models import EngageSrc, EngageDest

import adapter.ticketing.engage

import packages.load_web3 as load_web3
import packages.load_config as load_config

from .contract_api import get_contract

config = load_config.load_config()

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

import logging

logger = logging.getLogger(__name__)

def get_tickets(contract_idx, start_date, end_date):
    try:
        contract = get_contract(contract_idx)
        tickets = []

        if contract["contract_type"] == "ticketing":
            if contract["extended_data"].get("provider") == "engage":
                try:
                    engage_src = EngageSrc.objects.get(src_code=contract["extended_data"]["src_code"])
                    engage_dest = EngageDest.objects.get(dest_code=contract["extended_data"]["dest_code"])
                    tickets = adapter.ticketing.engage.get_tickets(contract, engage_src, engage_dest, start_date, end_date)
                except ObjectDoesNotExist as e:
                    logger.error(f"Engage source or destination not found for contract {contract_idx}: {str(e)}")
                    raise ValueError(f"Engage source or destination not found for contract {contract_idx}") from e

        return tickets

    except Exception as e:
        logger.error(f"Error retrieving tickets for contract {contract_idx}: {str(e)}")
        raise RuntimeError(f"Failed to retrieve tickets for contract {contract_idx}") from e