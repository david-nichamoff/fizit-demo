from django.shortcuts import render
from api.managers import ConfigManager, SecretsManager
import logging
import requests

logger = logging.getLogger(__name__)

def view_contract_view(request, extra_context=None):
    """
    Render the View Contract page with details about the specified contract.
    """
    try:
        # Get contract_idx from query parameters
        contract_idx = request.GET.get("contract_idx")
        if not contract_idx:
            return render(
                request,
                "admin/view_contract.html",
                {"error": "Please provide a contract index (contract_idx)."},
                status=400,
            )

        # Initialize Config and Secrets Managers
        config_manager = ConfigManager()
        secrets_manager = SecretsManager()
        config = config_manager.load_config()
        keys = secrets_manager.load_keys()

        headers = {
            "Authorization": f"Api-Key {keys['FIZIT_MASTER_KEY']}",
            "Content-Type": "application/json",
        }

        # Fetch data
        base_url = config["url"]
        contract_data = _fetch_data(f"{base_url}/api/contracts/{contract_idx}/", headers)
        settlements = _fetch_data(f"{base_url}/api/contracts/{contract_idx}/settlements/", headers)
        parties = _fetch_data(f"{base_url}/api/contracts/{contract_idx}/parties/", headers)
        transactions = _fetch_data(f"{base_url}/api/contracts/{contract_idx}/transactions/", headers)
        artifacts = _fetch_data(f"{base_url}/api/contracts/{contract_idx}/artifacts/", headers)

        # Combine data into context
        context = {
            "contract_data": contract_data,
            "settlements": settlements,
            "parties": parties,
            "transactions": transactions,
            "artifacts": artifacts,
            "contract_idx": contract_idx,
        }

        # Merge with extra_context if provided
        if extra_context:
            context.update(extra_context)

        return render(request, "admin/view_contract.html", context)

    except Exception as e:
        logger.error(f"Error in view_contract: {e}")
        return render(
            request,
            "admin/view_contract.html",
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