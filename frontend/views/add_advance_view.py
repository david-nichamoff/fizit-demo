import requests
import logging
import json

from datetime import datetime

from django.contrib import messages
from django.shortcuts import render, redirect

from api.managers import ConfigManager, SecretsManager
from api.operations import CsrfOperations, BankOperations, ContractOperations
from frontend.forms import AdvanceForm

from api.utilities.logging import log_info, log_warning, log_error

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
def fetch_all_contracts(headers, config):

    contract_ops = ContractOperations(headers, config)

    # Get the total contract count
    try:
        count_response = contract_ops.get_count()
    except Exception as e:
        log_error(logger, f"Failed to fetch contract count: {e}")
        return []

    contract_count = count_response['count']

    # Fetch contracts one by one
    contracts = []
    for contract_idx in range(0, contract_count):
        try:
            contract = contract_ops.get_contract(contract_idx)
            contracts.append(contract)
        except Exception as e:
            log_error(logger, f"Failed to fetch contract {contract_idx}: {e}")

    return contracts

def fetch_all_advances(headers, config):
    bank_ops = BankOperations(headers, config)
    contract_ops = ContractOperations(headers, config)

    # Get the total contract count
    try:
        count_response = contract_ops.get_count()
    except requests.RequestException as e:
        log_error(logger, f"Failed to fetch contract count: {e}")
        return []

    contract_count = count_response['count']

    # Fetch advances one by one
    advances = []
    for contract_idx in range(0, contract_count):
        
        try:
            advance = bank_ops.get_advances(contract_idx)
            advances.extend(advance)

        except requests.RequestException as e:
            log_warning(logger, f"Failed to fetch advances for contract {contract_idx}: {e}")

    return advances

def handle_post_request(request, headers, config):

    csrf_ops = CsrfOperations(headers, config)
    csrf_token = csrf_ops.get_csrf_token()

    bank_ops = BankOperations(headers, config, csrf_token)

    try:
        # Retrieve selected advances from the form
        contract_idx = request.POST.get("contract_idx")
        advances_json = request.POST.get("advances")

        if not contract_idx or not advances_json:
            messages.error(request, "No contract or advances selected.")
            return redirect(request.path)

        advances_to_post = json.loads(advances_json)

        if not advances_to_post:
            messages.error(request, "No valid advances found for posting.")
            return redirect(request.path)

        add_advance_response = bank_ops.post_advances(contract_idx, advances_to_post)

        if "error" not in add_advance_response:
            messages.success(request, "Advances posted successfully.")
        else:
            log_error(logger, f"Failed to post advances: {add_advance_response.json()}")
            messages.error(request, f"Failed to post advances: {add_advance_response.json().get('error', 'Unknown error')}")

    except Exception as e:
        logger.exception(f"Unexpected error while posting advances: {e}")
        messages.error(request, f"An unexpected error occurred: {str(e)}")

    return redirect(request.path)

def group_advances_by_contract(advances):
    """Group advances by contract_idx using a standard dictionary."""
    grouped_advances = {}
    for advance in advances:
        contract_idx = advance["contract_idx"]
        if contract_idx not in grouped_advances:
            grouped_advances[contract_idx] = []  # Initialize an empty list for the contract
        grouped_advances[contract_idx].append(advance)
    return grouped_advances  # Return a plain dictionary

# Main view
def add_advance_view(request, extra_context=None):
    headers, config = initialize_backend_services()

    if request.method == 'POST':
        # Delegate to the POST handler
        return handle_post_request(request, headers, config)

    # Fetch all contracts with prepopulated transact_data
    advances = fetch_all_advances(headers, config)

    # Group advances by contract_idx for the dropdown and table
    grouped_advances = group_advances_by_contract(advances)

    # Fetch all contracts with prepopulated transact_data
    raw_contracts = fetch_all_contracts(headers, config)

    contracts = [
        {
            "contract_idx": contract["contract_idx"],
            "contract_name": contract["contract_name"],
        }

        for contract in raw_contracts
    ]

    # Initialize the form with contract data
    advance_form = AdvanceForm(contracts=contracts)

    context = {
        "advance_form": advance_form,
        "contracts": contracts,  # Used for the contract dropdown
        "advances_by_contract": grouped_advances,  # Used for populating tables dynamically
    }

    if extra_context:
        context.update(extra_context)

    return render(request, "admin/add_advance.html", context)