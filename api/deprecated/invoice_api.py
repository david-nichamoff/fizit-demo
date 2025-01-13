import logging
from datetime import datetime
from rest_framework import status

from api.managers import Web3Manager, ConfigManager
from api.interfaces import ContractAPI

from api.utilities.logging import  log_error, log_info, log_warning

class InvoiceAPI:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure that the class is a singleton."""
        if not cls._instance:
            cls._instance = super(InvoiceAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize with Web3Manager, ConfigManager, and logger."""
        if not hasattr(self, "initialized"):
            self.config_manager = ConfigManager()
            self.config = self.config_manager.load_config()
            self.w3_manager = Web3Manager()
            self.contract_api = ContractAPI()

            self.logger = logging.getLogger(__name__)
            self.initialized = True

    def get_contract_invoices(self, contract_idx: int, start_date: datetime, end_date: datetime):
        """Retrieve invoices for a given contract."""
        try:
            contract = self.contract_api.get_contract(contract_idx)

            if contract["contract_type"] == "ticketing":
                provider = contract["extended_data"].get("provider")
                if provider == "engage":
                    invoices = self._get_engage_invoices(contract, start_date, end_date)
                    return {
                        "status": status.HTTP_200_OK,
                        "data": invoices,
                    }
                else:
                    error_message = f"Unsupported provider '{provider}' for contract {contract_idx}."
                    self.log_error(logger, error_message, extra={"operation": "get_contract_invoices", "contract_idx": contract_idx})
                    return {
                        "status": status.HTTP_400_BAD_REQUEST,
                        "error": "UnsupportedProvider",
                        "message": error_message,
                    }

            error_message = f"Unsupported contract type '{contract['contract_type']}' for contract {contract_idx}."
            self.log_warning(logger, error_message, extra={"operation": "get_contract_invoices", "contract_idx": contract_idx})
            return {
                "status": status.HTTP_400_BAD_REQUEST,
                "error": "UnsupportedContractType",
                "message": error_message,
            }

        except Exception as e:
            error_message = f"Error retrieving invoices for contract {contract_idx}: {str(e)}"
            self.log_error(logger, error_message, exc_info=True, extra={"operation": "get_contract_invoices", "contract_idx": contract_idx})
            return {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error": "InvoiceRetrievalError",
                "message": error_message,
            }

    def _get_engage_invoices(self, contract: dict, start_date: datetime, end_date: datetime):
        """Retrieve invoices from Engage provider."""
        try:
            engage_src, engage_dest = self._get_engage_src_dest(contract)
            invoices = engage_adapter.get_invoices(contract, engage_src, engage_dest, start_date, end_date)
            self.log_info(logger, 
                f"Retrieved {len(invoices)} invoices for Engage provider.",
                extra={"operation": "_get_engage_invoices", "contract_idx": contract["contract_idx"]},
            )
            return invoices
        except ValueError as e:
            error_message = f"Validation error in Engage provider for contract {contract['contract_idx']}: {str(e)}"
            self.log_error(logger, error_message, exc_info=True, extra={"operation": "_get_engage_invoices", "contract_idx": contract["contract_idx"]})
            raise RuntimeError({
                "status": status.HTTP_400_BAD_REQUEST,
                "error": "ValidationError",
                "message": error_message,
            }) from e
        except Exception as e:
            error_message = f"Unexpected error in Engage provider: {str(e)}"
            self.log_error(logger, error_message, exc_info=True, extra={"operation": "_get_engage_invoices", "contract_idx": contract["contract_idx"]})
            raise RuntimeError({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error": "EngageError",
                "message": error_message,
            }) from e

    def _get_engage_src_dest(self, contract: dict):
        """Retrieve Engage source and destination objects."""
        try:
            src_code = contract["extended_data"].get("src_code")
            dest_code = contract["extended_data"].get("dest_code")

            if not src_code or not dest_code:
                error_message = "Both 'src_code' and 'dest_code' must be provided in contract's extended data."
                self.log_error(logger, error_message, extra={"operation": "_get_engage_src_dest", "contract_idx": contract["contract_idx"]})
                raise ValueError(error_message)

            engage_src = EngageSrc.objects.get(src_code=src_code)
            engage_dest = EngageDest.objects.get(dest_code=dest_code)
            self.log_info(logger, 
                f"Engage source and destination retrieved: {src_code}, {dest_code}",
                extra={"operation": "_get_engage_src_dest", "contract_idx": contract["contract_idx"]},
            )
            return engage_src, engage_dest

        except EngageSrc.DoesNotExist:
            error_message = f"EngageSrc not found for src_code: {src_code}"
            self.log_error(logger, error_message, exc_info=True, extra={"operation": "_get_engage_src_dest", "contract_idx": contract["contract_idx"]})
            raise RuntimeError({
                "status": status.HTTP_400_BAD_REQUEST,
                "error": "SourceNotFound",
                "message": error_message,
            }) from e
        except EngageDest.DoesNotExist:
            error_message = f"EngageDest not found for dest_code: {dest_code}"
            self.log_error(logger, error_message, exc_info=True, extra={"operation": "_get_engage_src_dest", "contract_idx": contract["contract_idx"]})
            raise RuntimeError({
                "status": status.HTTP_400_BAD_REQUEST,
                "error": "DestinationNotFound",
                "message": error_message,
            }) from e
        except Exception as e:
            error_message = f"Error retrieving Engage source/destination: {str(e)}"
            self.log_error(logger, error_message, exc_info=True, extra={"operation": "_get_engage_src_dest", "contract_idx": contract["contract_idx"]})
            raise RuntimeError({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error": "EngageSourceDestinationError",
                "message": error_message,
            }) from e