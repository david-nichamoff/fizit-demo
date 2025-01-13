import logging
import requests

from datetime import datetime, timedelta

from django.contrib import messages
from api.managers import ConfigManager, SecretsManager
from api.operations import BankOperations, ContractOperations
from frontend.forms import FindDepositsForm
from django.shortcuts import render, redirect

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

# Helper function to fetch all contracts
def fetch_all_contracts(headers, config):
    contract_ops = ContractOperations(headers, config)

    try:
        contract_response = contract_ops.get_count()

        if "error" in contract_response:
            raise Exception
        else:
            contract_count = contract_response["count"]

    except Exception as e:
        log_error(logger, f"Failed to fetch contract count: {e}")
        return []

    contracts = []
    for contract_idx in range(contract_count):
        try:
            contract = contract_ops.get_contract(contract_idx)
            contracts.append(contract)
        except Exception as e:
            log_warning(logger, f"Failed to fetch contract {contract_idx}: {e}")

    return contracts

# Helper function to fetch deposits
def fetch_deposits(headers, config, contract_idx, start_date, end_date):
    operations = BankOperations(headers, config)

    try:
        deposits = operations.get_deposits(contract_idx, start_date, end_date)
        return deposits
    except Exception as e:
        log_error(logger, f"Failed to fetch deposits for contract {contract_idx}: {e}")
        return []

def handle_find_deposits(request, headers, config, contracts):
    find_deposits_form = FindDepositsForm(request.POST, contracts=contracts)
    deposits = []
    selected_contract_idx = None

    if find_deposits_form.is_valid():
        # Extract validated data
        contract_idx = find_deposits_form.cleaned_data["contract_idx"]
        start_date = find_deposits_form.cleaned_data["start_date"]
        end_date = find_deposits_form.cleaned_data["end_date"]

        # Fetch deposits
        deposits = fetch_deposits(headers, config, contract_idx, start_date, end_date)
        selected_contract_idx = contract_idx

        log_info(logger, f"Found deposits: {deposits} for selected contract {selected_contract_idx}")

        # Store in session
        request.session['deposits'] = deposits
        request.session['selected_contract_idx'] = selected_contract_idx

        # Set success or no deposits message
        if deposits:
            messages.success(request, "Deposits fetched successfully.")
        else:
            messages.success(request, "No deposits found for this contract.")
    else:
        messages.error(request, "Invalid data for finding deposits.")

    return find_deposits_form, deposits, selected_contract_idx

# View for finding deposits
def find_deposits_view(request, extra_context=None):
    headers, config = initialize_backend_services()

    # Fetch contracts for dropdown
    raw_contracts = fetch_all_contracts(headers, config)
    contracts = [{"contract_idx": c["contract_idx"], "contract_name": c["contract_name"]} for c in raw_contracts]

    # Initialize form and variables
    find_deposits_form = FindDepositsForm(contracts=contracts, initial={
        "start_date": (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%dT%H:%M:%S'),
        "end_date": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
    })
    deposits = []
    selected_contract_idx = None

    if request.method == 'POST' and "find_deposits" in request.POST:
        find_deposits_form, deposits, selected_contract_idx = handle_find_deposits(request, headers, config, contracts)

    # Prepare context for the template
    context = {
        "find_deposits_form": find_deposits_form,
        "contracts": contracts,
        "deposits": deposits,
        "selected_contract_idx": selected_contract_idx,
    }

    # Merge with extra_context if provided
    if extra_context:
        context.update(extra_context)

    return render(request, "admin/find_deposits.html", context)