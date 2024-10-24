import logging
from django.core.exceptions import ObjectDoesNotExist

from api.managers import Web3Manager, ConfigManager
from api.interfaces import ContractAPI

import api.adapters.ticketing.engage as engage_adapter

class TicketAPI:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure the class follows the Singleton pattern."""
        if not cls._instance:
            cls._instance = super(TicketAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize the TicketAPI class with configurations and logger."""
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.w3_manager = Web3Manager()
        self.contract_api = ContractAPI()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

    def get_tickets(self, contract_idx, start_date, end_date):
        """Retrieve tickets based on the contract type and provider."""
        try:
            contract = self.contract_api.get_contract(contract_idx)
            tickets = []

            if contract["contract_type"] == "ticketing":
                if contract["extended_data"].get("provider") == "engage":
                    engage_src, engage_dest = self._get_engage_sources(contract)
                    tickets = engage_adapter.get_tickets(contract, engage_src, engage_dest, start_date, end_date)

            return tickets

        except Exception as e:
            self.logger.error(f"Error retrieving tickets for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to retrieve tickets for contract {contract_idx}") from e

    def _get_engage_sources(self, contract):
        """Retrieve Engage source and destination objects."""
        """
        try:
            engage_src = EngageSrc.objects.get(src_code=contract["extended_data"]["src_code"])
            engage_dest = EngageDest.objects.get(dest_code=contract["extended_data"]["dest_code"])
            return engage_src, engage_dest
        except ObjectDoesNotExist as e:
            self.logger.error(f"Engage source or destination not found for contract {contract['contract_idx']}: {str(e)}")
            raise ValueError(f"Engage source or destination not found for contract {contract['contract_idx']}") from e
        """