from django.shortcuts import render, redirect
from django.contrib import messages
from api.managers import ConfigManager, SecretsManager
from api.operations import BankOperations
from frontend.forms import DepositForm

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
def fetch_all_deposits(headers, config):
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

    # Fetch deposits one by one
    deposits = []
    for contract_idx in range(0, contract_count):
        try:
            deposit_response = operations.get_deposits(contract_idx)
            deposit_response.raise_for_status()
            deposits = deposit_response.json()
            deposits.append(deposits)
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch contract {contract_idx}: {e}")

    return deposits

# Handle POST request
def handle_post_request(request, headers, config):
    contract_idx = request.POST.get("contract_idx")

    if not contract_idx:
        messages.error(request, "All fields are required.")
        return redirect(request.path)

# Main view
def add_deposit_view(request, extra_context=None):
    headers, config = initialize_backend_services()

    if request.method == 'POST':
        # Delegate to the POST handler
        return handle_post_request(request, headers, config)

    # Fetch all contracts with prepopulated transact_data
    deposits = fetch_all_deposits(headers, config)

    # Initialize the form with contract data
    deposit_form = DepositForm(deposits=deposits)

    logger.info(f"deposits: {deposits}")

    context = {
        "deposit_form": deposit_form,
        "deposits": deposits
    }
    if extra_context:
        context.update(extra_context)

    return render(request, "admin/add_deposit.html", context)