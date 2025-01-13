import requests
import logging
import json

from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib import messages

from api.managers import ConfigManager, SecretsManager
from api.operations import BankOperations, CsrfOperations, ContractOperations
from frontend.forms import ResidualForm

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
        except requests.RequestException as e:
            log_warning(logger, f"Failed to fetch contract {contract_idx}: {e}")

    return contracts

def fetch_all_residuals(headers, config):
    bank_ops = BankOperations(headers, config)
    contract_ops = ContractOperations(headers, config)

    # Get the total contract count
    try:
        count_response = contract_ops.get_count()
    except Exception as e:
        log_error(logger, f"Failed to fetch contract count: {e}")
        return []

    contract_count = count_response['count']

    # Fetch residuals one by one
    residuals = []
    for contract_idx in range(0, contract_count):
        try:
            residuals = bank_ops.get_residuals(contract_idx)
        except requests.RequestException as e:
            log_warning(logger, f"Failed to fetch contract {contract_idx}: {e}")

    return residuals

def handle_post_request(request, headers, config):

    csrf_ops = CsrfOperations(headers, config)
    csrf_token = csrf_ops.get_csrf_token()
    bank_ops = BankOperations(headers, config, csrf_token)

    try:
        # Retrieve selected advances from the form
        contract_idx = request.POST.get("contract_idx")
        residuals_json = request.POST.get("residuals")

        if not contract_idx or not residuals_json:
            messages.error(request, "No contract or residuals selected.")
            return redirect(request.path)

        residuals_to_post = json.loads(residuals_json)

        if not residuals_to_post:
            messages.error(request, "No valid residuals found for posting.")
            return redirect(request.path)

        add_residual_response = bank_ops.post_residuals(contract_idx, residuals_to_post)

        if add_residual_response.status_code == 201:
            messages.success(request, "Residuals posted successfully.")
        else:
            log_error(logger, f"Failed to post residuals: {add_residual_response.json()}")
            messages.error(request, f"Failed to post residuals: {add_residual_response.json().get('error', 'Unknown error')}")

    except Exception as e:
        logger.exception(f"Unexpected error while posting residuals: {e}")
        messages.error(request, f"An unexpected error occurred: {str(e)}")

    return redirect(request.path)

def group_residuals_by_contract(residuals):
    """Group residuals by contract_idx using a standard dictionary."""
    grouped_residuals = {}
    for residual in residuals:
        contract_idx = residual["contract_idx"]
        if contract_idx not in grouped_residuals:
            grouped_residuals[contract_idx] = []  # Initialize an empty list for the contract
        grouped_residuals[contract_idx].append(residual)
    return grouped_residuals  # Return a plain dictionary

# Main view
def add_residual_view(request, extra_context=None):
    headers, config = initialize_backend_services()

    if request.method == 'POST':
        # Delegate to the POST handler
        return handle_post_request(request, headers, config)

    # Fetch all contracts with prepopulated transact_data
    residuals = fetch_all_residuals(headers, config)

    # Group advances by contract_idx for the dropdown and table
    grouped_residuals = group_residuals_by_contract(residuals)

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
    residual_form = ResidualForm(contracts=contracts)

    context = {
        "residual_form": residual_form,
        "contracts": contracts,  # Used for the contract dropdown
        "residuals_by_contract": grouped_residuals  # Used for populating tables dynamically
    }

    if extra_context:
        context.update(extra_context)

    return render(request, "admin/add_residual.html", context)