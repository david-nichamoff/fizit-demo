import logging
import requests

from django.shortcuts import render
from api.managers import ConfigManager, SecretsManager
from api.operations import ContractOperations
from rest_framework import status
from django.contrib import messages

from api.utilities.logging import log_info, log_warning, log_error

logger = logging.getLogger(__name__)

def list_contracts_view(request, extra_context=None):
    """
    Render the List Contracts page displaying all contracts in a grid.
    """
    try:
        # Initialize Config and Secrets Managers
        config_manager = ConfigManager()
        secrets_manager = SecretsManager()
        config = config_manager.load_config()
        keys = secrets_manager.load_keys()

        headers = {
            "Authorization": f"Api-Key {keys['FIZIT_MASTER_KEY']}",
            "Content-Type": "application/json",
        }

        contract_ops = ContractOperations(headers, config)

        try:
            response = contract_ops.get_count()
            contract_count = response.get("count")
        except Exception as e:
            error_message = f"Failed to fetch count of contracts"
            log_error(logger, f"{error_message}: {e}")
            messages.error(request, f"{error_message}")

        contracts = []
        for contract_idx in range(contract_count):
            try:
                response = contract_ops.get_contract(contract_idx)
                contracts.append(response)
            except Exception as e:
                error_message = f"Failed to fetch contract {contract_idx}"
                log_error(logger, f"{error_message}: {e}")
                messages.error(request, f"{error_message}")

        # Handle sorting
        ordering = request.GET.get("ordering", "contract_idx")  # Default to 'contract_idx'
        reverse = ordering.startswith("-")
        ordering_field = ordering.lstrip("-")

        # Sort contracts if the field exists in the contract data
        if contracts and ordering_field in contracts[0]:
            contracts = sorted(contracts, key=lambda x: x.get(ordering_field, ""), reverse=reverse)

        # Prepare sorting links for the template
        sorting_links = {
            "contract_idx": f"?ordering={'-' if ordering == 'contract_idx' else ''}contract_idx",
            "contract_name": f"?ordering={'-' if ordering == 'contract_name' else ''}contract_name",
            "contract_type": f"?ordering={'-' if ordering == 'contract_type' else ''}contract_type",
            "is_quote": f"?ordering={'-' if ordering == 'is_quote' else ''}is_quote",
            "is_active": f"?ordering={'-' if ordering == 'is_active' else ''}is_active",
        }

        # Prepare context
        context = {
            "contracts": contracts,
            "ordering": ordering,
            "sorting_links": sorting_links,
        }

        # Merge with extra_context if provided
        if extra_context:
            context.update(extra_context)

        log_info(logger, f"Context for list_contracts.html: {context}")
        return render(request, "admin/list_contracts.html", context)

    except Exception as e:
        error_message = f"Error in list_contract_view"
        log_error(logger, f"{error_message}: {e}")
        return render(request, "admin/list_contract.html", error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)