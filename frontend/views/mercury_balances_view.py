import logging
import requests

from rest_framework import status
from django.shortcuts import render

from api.config import ConfigManager
from api.secrets import SecretsManager
from api.operations import BankOperations

from api.utilities.logging import log_info, log_warning, log_error

logger = logging.getLogger(__name__)

def mercury_balances_view(request, extra_context=None):
    """
    Custom view to display Mercury account balances.
    """
    try:
        log_info(logger, "Mercury Balances view accessed")

        # Initialize Config and Secrets Managers
        config_manager = ConfigManager()
        secrets_manager = SecretsManager()

        headers = {
            'Authorization': f"Api-Key {keys['FIZIT_MASTER_KEY']}",
            'Content-Type': 'application/json',
        }

        # Fetch the API key from secrets
        api_key = keys.get("FIZIT_MASTER_KEY")
        if not api_key:
            log_error(logger, "API key not found in secrets.")
            return render(
                request,
                "admin/mercury_balances.html",
                {"error": "API key not configured."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        bank_ops = BankOperations(headers, config) 
        accounts = bank_ops.get_accounts("mercury")

        if "error" in accounts:
            log_error(logger, f"API request failed with error {accounts["error"]}")
            return render(
                request,
                "admin/mercury_balances.html",
                {"error": f"Failed to fetch accounts. Status code: {accounts["error"]}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Parse the response data
        if not isinstance(accounts, list):
            log_error(logger, "Unexpected response format from accounts API.")
            return render(
                request,
                "admin/mercury_balances.html",
                {"error": "Unexpected response format from accounts API."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Prepare the context
        context = {"accounts": accounts}

        # Merge with extra_context if provided
        if extra_context:
            context.update(extra_context)

        # Render the template
        return render(request, "admin/mercury_balances.html", context)

    except Exception as e:
        log_error(logger, f"Error in mercury_balances_view: {e}")
        return render(
            request,
            "admin/mercury_balances.html",
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )