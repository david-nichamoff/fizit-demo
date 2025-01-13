import logging
from rest_framework import status
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
        if not hasattr(self, "initialized"):  # Ensure init runs only once
            self.config_manager = ConfigManager()
            self.config = self.config_manager.load_config()
            self.w3_manager = Web3Manager()
            self.contract_api = ContractAPI()

            self.logger = logging.getLogger(__name__)
            self.initialized = True  # Mark this instance as initialized

    def get_tickets(self, contract_idx, start_date, end_date):
        """Retrieve tickets for a given contract based on its type and provider."""
        try:
            contract = self.contract_api.get_contract(contract_idx)
            if contract["contract_type"] != "ticketing":
                self.log_warning(logger, 
                    f"Unsupported contract type '{contract['contract_type']}' for tickets in contract {contract_idx}."
                )
                return {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "error": "UnsupportedContractType",
                    "message": f"Contract type '{contract['contract_type']}' is not supported for tickets.",
                }

            tickets = self._get_tickets_from_provider(contract, start_date, end_date)
            self.log_info(logger, f"Retrieved {len(tickets)} tickets for contract {contract_idx}.")
            return {
                "status": status.HTTP_200_OK,
                "data": tickets,
            }
        except Exception as e:
            error_message = f"Error retrieving tickets for contract {contract_idx}: {e}"
            self.log_error(logger, error_message, exc_info=True, extra={"operation": "get_tickets", "contract_idx": contract_idx})
            return {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error": "TicketRetrievalError",
                "message": error_message,
            }

    def _get_tickets_from_provider(self, contract, start_date, end_date):
        """Get tickets from the provider based on the contract details."""
        try:
            provider = contract["extended_data"].get("provider")
            if provider == "engage":
                engage_src, engage_dest = self._get_engage_sources(contract)
                return engage_adapter.get_tickets(contract, engage_src, engage_dest, start_date, end_date)
            else:
                self.log_warning(logger, f"Unsupported provider '{provider}' for contract {contract['contract_idx']}.")
                raise ValueError(f"Unsupported provider: {provider}")
        except ValueError as e:
            self.log_error(logger, f"Validation error in provider logic for contract {contract['contract_idx']}: {e}")
            raise
        except Exception as e:
            error_message = f"Error retrieving tickets from provider '{provider}' for contract {contract['contract_idx']}: {e}"
            self.log_error(logger, error_message, exc_info=True, extra={"operation": "_get_tickets_from_provider"})
            raise RuntimeError(f"Failed to retrieve tickets from provider '{provider}' for contract {contract['contract_idx']}") from e

    def _get_engage_sources(self, contract):
        """Retrieve Engage source and destination objects based on the contract."""
        try:
            # Example implementation: Adjust based on your actual EngageSrc/EngageDest models
            engage_src = EngageSrc.objects.get(src_code=contract["extended_data"]["src_code"])
            engage_dest = EngageDest.objects.get(dest_code=contract["extended_data"]["dest_code"])
            self.log_info(logger, 
                f"Engage source and destination retrieved for contract {contract['contract_idx']}: {engage_src}, {engage_dest}."
            )
            return engage_src, engage_dest
        except ObjectDoesNotExist as e:
            error_message = f"Engage source or destination not found for contract {contract['contract_idx']}: {e}"
            self.log_error(logger, error_message, exc_info=True, extra={"operation": "_get_engage_sources"})
            raise RuntimeError(f"Failed to retrieve Engage source/destination for contract {contract['contract_idx']}") from e
        except Exception as e:
            error_message = f"Unexpected error retrieving Engage source/destination for contract {contract['contract_idx']}: {e}"
            self.log_error(logger, error_message, exc_info=True, extra={"operation": "_get_engage_sources"})
            raise RuntimeError(f"Failed to retrieve Engage source/destination for contract {contract['contract_idx']}") from e