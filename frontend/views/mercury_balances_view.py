from django.shortcuts import render
from api.managers import ConfigManager, SecretsManager
import logging
import requests

logger = logging.getLogger(__name__)

def mercury_balances_view(request, extra_context=None):
    """
    Custom view to display Mercury account balances.
    """
    try:
        logger.info("Mercury Balances view accessed")

        # Initialize Config and Secrets Managers
        config_manager = ConfigManager()
        secrets_manager = SecretsManager()
        config = config_manager.load_config()
        keys = secrets_manager.load_keys()

        # Fetch the API key from secrets
        api_key = keys.get("FIZIT_MASTER_KEY")
        if not api_key:
            logger.error("API key not found in secrets.")
            return render(
                request,
                "admin/mercury_balances.html",
                {"error": "API key not configured."},
                status=500,
            )

        # Construct the API endpoint
        base_url = config.get("url")
        if not base_url:
            logger.error("Base URL not found in configuration.")
            return render(
                request,
                "admin/mercury_balances.html",
                {"error": "Base URL not configured."},
                status=500,
            )
        accounts_url = f"{base_url}/api/accounts/?bank=mercury"

        # Make the API call to fetch accounts
        headers = {"Authorization": f"Api-Key {api_key}"}
        logger.info(f"Fetching accounts from {accounts_url}")
        response = requests.get(accounts_url, headers=headers)

        if response.status_code != 200:
            logger.error(f"API request failed with status {response.status_code}")
            return render(
                request,
                "admin/mercury_balances.html",
                {"error": f"Failed to fetch accounts. Status code: {response.status_code}"},
                status=response.status_code,
            )

        # Parse the response data
        accounts = response.json()
        if not isinstance(accounts, list):
            logger.error("Unexpected response format from accounts API.")
            return render(
                request,
                "admin/mercury_balances.html",
                {"error": "Unexpected response format from accounts API."},
                status=500,
            )

        # Prepare the context
        context = {"accounts": accounts}

        # Merge with extra_context if provided
        if extra_context:
            context.update(extra_context)

        # Render the template
        return render(request, "admin/mercury_balances.html", context)

    except Exception as e:
        logger.error(f"Error in mercury_balances_view: {e}")
        return render(
            request,
            "admin/mercury_balances.html",
            {"error": f"An error occurred: {str(e)}"},
            status=500,
        )