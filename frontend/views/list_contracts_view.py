from django.shortcuts import render
from api.managers import ConfigManager, SecretsManager
import logging
import requests

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

        # Fetch all contracts
        base_url = config["url"]
        contracts = _fetch_data(f"{base_url}/api/contracts/", headers)

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

        return render(request, "admin/list_contracts.html", context)

    except Exception as e:
        logger.error(f"Error in list_contracts_view: {e}")
        return render(
            request,
            "admin/list_contracts.html",
            {"error": f"An error occurred: {str(e)}"},
            status=500,
        )


def _fetch_data(url, headers):
    """
    Helper function to fetch data from an API endpoint.
    """
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()