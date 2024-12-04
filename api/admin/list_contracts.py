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

        # Prepare context
        context = {
            "contracts": contracts,
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