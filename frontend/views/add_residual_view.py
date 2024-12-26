from django.shortcuts import render, redirect
from django.contrib import messages
from api.managers import ConfigManager, SecretsManager
from api.operations import BankOperations
from frontend.forms import ResidualForm

from datetime import datetime

import requests
import logging

logger = logging.getLogger(__name__)

# Helper function to initialize headers and configuration
def initialize_backend_services():
    secrets_manager = SecretsManager()
    config_manager = ConfigManager()
    keys = secrets_manager.load_keys()
    headers = {
        'Authorization': f"Api-Key {keys['FIZIT_MASTER_KEY']}",
        'Content-Type': 'application/json',
    }
    config = config_manager.load_config()
    return headers, config

# Fetch total contract count and fetch each contract one by one
def fetch_all_residuals(headers, config):
    base_url = config["url"]
    logger.info(f"base_url: {base_url}")
    operations = BankOperations(headers, config)

    # Get the total contract count
    count_url = f"{base_url}/api/contracts/count/"
    try:
        count_response = requests.get(count_url, headers=headers)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch contract count: {e}")
        return []

    contract_count = count_response.json()['contract_count']

    # Fetch residuals one by one
    residuals = []
    for contract_idx in range(0, contract_count):
        try:
            residual_response = operations.get_residuals(contract_idx)
            residual_response.raise_for_status()
            residuals = residual_response.json()
            residuals.append(residuals)
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch contract {contract_idx}: {e}")

    return residuals

# Handle POST request
def handle_post_request(request, headers, config):
    contract_idx = request.POST.get("contract_idx")

    if not contract_idx:
        messages.error(request, "All fields are required.")
        return redirect(request.path)

# Main view
def add_residual_view(request, extra_context=None):
    headers, config = initialize_backend_services()

    if request.method == 'POST':
        # Delegate to the POST handler
        return handle_post_request(request, headers, config)

    # Fetch all contracts with prepopulated transact_data
    residuals = fetch_all_residuals(headers, config)

    # Initialize the form with contract data
    residual_form = ResidualForm(residuals=residuals)

    logger.info(f"residuals: {residuals}")

    context = {
        "residual_form": residual_form,
        "residuals": residuals
    }
    if extra_context:
        context.update(extra_context)

    return render(request, "admin/add_residual.html", context)