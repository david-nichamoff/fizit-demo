import logging

from api.managers import Web3Manager, ConfigManager
from api.interfaces import ContractAPI

import api.adapters.ticketing.engage as engage_adapter

class InvoiceAPI:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure that the class is a singleton."""
        if not cls._instance:
            cls._instance = super(InvoiceAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize with Web3Manager, ConfigManager, and logger."""
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.web3_manager = Web3Manager()
        self.w3 = self.web3_manager.get_web3_instance()
        self.w3_contract = self.web3_manager.get_web3_contract()
        self.contract_api = ContractAPI()

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

    def get_contract_invoices(self, contract_idx, start_date, end_date):
        """Retrieve invoices for a contract based on contract type and provider."""
        try:
            contract = self.contract_api.get_contract(contract_idx)

            if contract["contract_type"] == "ticketing": 
                provider = contract["extended_data"].get("provider")
                if provider == "engage":
                    engage_src, engage_dest = self._get_engage_src_dest(contract)
                    invoices = engage_adapter.get_invoices(contract, engage_src, engage_dest, start_date, end_date)
                    return invoices
                else:
                    self.logger.error(f"Unsupported provider: {provider}")
                    raise ValueError(f"Unsupported provider: {provider}")

            self.logger.warning(f"No invoices retrieved for contract {contract_idx} due to unsupported contract type.")
            return []

        except Exception as e:
            self.logger.error(f"Error retrieving invoices for contract {contract_idx}: {str(e)}")
            raise RuntimeError(f"Failed to retrieve invoices for contract {contract_idx}") from e

    def _get_engage_src_dest(self, contract):
        """Retrieve the EngageSrc and EngageDest objects based on the contract data."""
        try:
            engage_src = EngageSrc.objects.get(src_code=contract["extended_data"]["src_code"])
            engage_dest = EngageDest.objects.get(dest_code=contract["extended_data"]["dest_code"])
            return engage_src, engage_dest
        except EngageSrc.DoesNotExist as e:
            self.logger.error(f"EngageSrc not found for src_code: {contract['extended_data']['src_code']}")
            raise ValueError(f"Source not found for src_code: {contract['extended_data']['src_code']}") from e
        except EngageDest.DoesNotExist as e:
            self.logger.error(f"EngageDest not found for dest_code: {contract['extended_data']['dest_code']}")
            raise ValueError(f"Destination not found for dest_code: {contract['extended_data']['dest_code']}") from e