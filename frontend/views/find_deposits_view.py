import logging
import requests
from datetime import datetime, timedelta

from django.contrib import messages
from django.shortcuts import render, redirect

from api.config import ConfigManager
from api.secrets import SecretsManager
from api.registry import RegistryManager
from api.operations import BankOperations, ContractOperations, CsrfOperations
from api.utilities.logging import log_info, log_warning, log_error

from frontend.forms import FindDepositsForm

logger = logging.getLogger(__name__)

# Helper function to initialize headers and configuration
def initialize_backend_services():
    secrets_manager = SecretsManager()
    config_manager = ConfigManager()
    registry_manager = RegistryManager()

    headers = {
        'Authorization': f"Api-Key {secrets_manager.get_master_key()}",
        'Content-Type': 'application/json',
    }

    csrf_ops = CsrfOperations(headers, config_manager.get_base_url())
    csrf_token = csrf_ops.get_csrf_token()

    return headers, registry_manager, config_manager, csrf_token


# Helper function to fetch all contracts
def fetch_all_contracts(request, headers, base_url, csrf_token):

    try:
        contract_ops = ContractOperations(headers, base_url, csrf_token)
        contracts = contract_ops.list_contracts()
        return contracts
    except Exception as e:
        error_message = f"Failed to get contract count"
        log_error(logger, f"{error_message}: {e}")
        messages.error(request, f"{error_message}")
        return []

# Helper function to fetch deposits
def fetch_deposits(headers, base_url, csrf_token, contract_type, contract_idx, start_date, end_date):

    try:
        operations = BankOperations(headers, base_url, csrf_token)
        deposits = operations.get_deposits(contract_type, contract_idx, start_date, end_date)
        return deposits
    except Exception as e:
        log_error(logger, f"Failed to fetch deposits for contract {contract_type}:{contract_idx}: {e}")
        return None

def handle_find_deposits(request, headers, base_url, csrf_token, contracts):
    find_deposits_form = FindDepositsForm(request.POST, contracts=contracts)
    deposits = []
    selected_contract_idx = None

    if find_deposits_form.is_valid():
        # Extract validated data
        contract_idx = find_deposits_form.cleaned_data["contract_idx"]
        contract_type = find_deposits_form.cleaned_data["contract_type"]
        start_date = find_deposits_form.cleaned_data["start_date"]
        end_date = find_deposits_form.cleaned_data["end_date"]

        log_info(logger, f"Fetching deposits with contract_idx: {contract_idx}")
        log_info(logger, f"Fetching deposits with contract_type: {contract_type}")

        # Fetch deposits
        deposits = fetch_deposits(headers, base_url, csrf_token, contract_type, contract_idx, start_date, end_date)
        selected_contract_idx = contract_idx

        if deposits is None:  # Detect failure
            messages.error(request, "An error occurred while fetching deposits. Please try again later.")
        elif not deposits:  # Valid response, but no deposits found
            messages.warning(request, "No deposits found for this contract.")
        else:
            messages.success(request, "Deposits fetched successfully.")

        log_info(logger, f"Found deposits: {deposits} for selected contract {selected_contract_idx}")

        # Store in session
        request.session['deposits'] = deposits
        request.session['selected_contract_idx'] = selected_contract_idx

    else:
        messages.error(request, "Invalid data for finding deposits.")

    return find_deposits_form, deposits, selected_contract_idx

# View for finding deposits
def find_deposits_view(request, extra_context=None):
    headers, registry_manager, config_manager, csrf_token = initialize_backend_services()
    base_url = config_manager.get_base_url()
    deposits = []

    # Fetch contracts for dropdown
    raw_contracts = fetch_all_contracts(request, headers, base_url, csrf_token)

    contracts = [
        {
            "contract_type": c["contract_type"],
            "contract_idx": c["contract_idx"],
            "contract_name": c["contract_name"]
        }
        for c in raw_contracts
        if registry_manager.get_deposit_api(c["contract_type"]) is not None 
    ]

    # Initialize form and variables
    find_deposits_form = FindDepositsForm(contracts=contracts, initial={
        "start_date": (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%dT%H:%M:%S'),
        "end_date": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
    })

    if request.method == 'POST':
        find_deposits_form, deposits, selected_contract_idx = handle_find_deposits(request, headers, base_url, csrf_token, contracts)

    contract_types = sorted(set(contract["contract_type"] for contract in contracts))

    # Prepare context for the template
    context = {
        "contracts": contracts,
        "deposits": deposits,
        "contract_types": contract_types,
        "default_contract_type": registry_manager.get_default_contract_type(),
        "find_deposits_form": find_deposits_form
    }

    if extra_context:
        context.update(extra_context)

    return render(request, "admin/find_deposits.html", context)