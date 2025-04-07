import json
import logging

from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib import messages

from api.operations import TransactionOperations, ContractOperations, CsrfOperations
from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_info, log_warning, log_error

from frontend.forms import TransactionForm

logger = logging.getLogger(__name__)

# Helper function to initialize headers and configuration
def initialize_backend_services():
    context = build_app_context()

    headers = {
        'Authorization': f"Api-Key {context.secrets_manager.get_master_key()}",
        'Content-Type': 'application/json',
    }

    csrf_ops = CsrfOperations(headers, context.config_manager.get_base_url())
    csrf_token = csrf_ops.get_csrf_token()

    return headers, context, csrf_token


# Fetch total contract count and fetch each contract one by one
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

# Recursive helper function to extract variables from transact_logic
def extract_transaction_variables(logic):
    variables = set()

    if isinstance(logic, dict):
        for key, value in logic.items():
            if key == "var" and isinstance(value, str):
                variables.add(value)
            else:
                variables.update(extract_transaction_variables(value))
    elif isinstance(logic, list):
        for item in logic:
            variables.update(extract_transaction_variables(item))

    return variables

# Handle POST request
def handle_post_request(request, headers, config, csrf_token):
    contract_idx = request.POST.get("contract_idx")
    contract_type = request.POST.get("contract_type")
    transact_dt = request.POST.get("transact_dt")
    transact_data_raw = request.POST.get("transact_data")

    if not contract_type or not contract_idx or not transact_dt or not transact_data_raw:
        messages.error(request, "All fields are required.")
        return redirect(request.path)

    try:
        # Parse transact_data from JSON
        transact_data = json.loads(transact_data_raw)
    except Exception as e:
        error_message = f"Invalid JSON in Transaction Data.  Please correct it and try again"
        log_error(logger, f"{error_message}: {e}")
        messages.error(request, f"{error_message}")
        return redirect(request.path)

    try:
        # Use TransactionOperations to post the transaction
        transaction_data = [{
            "extended_data": {},
            "transact_dt": transact_dt,
            "transact_data": transact_data,
        }]

        log_info(logger, f"Posting transaction {transaction_data}")
        transaction_ops = TransactionOperations(headers, config, csrf_token)
        response = transaction_ops.post_transactions(contract_type, contract_idx, transaction_data)

        # Check for response status
        if response["count"] > 0:
            messages.success(request, "Transaction added successfully.")
            return redirect(request.path)
        else:
            raise Exception 

    except Exception as e:
        error_message = f"Failed to add transaction"
        log_error(logger, f"{error_message}: {e}")
        messages.error(request, f"{error_message}: {e}")
        return redirect(request.path)

# Main view
def add_transaction_view(request, extra_context=None):
    headers, context, csrf_token = initialize_backend_services()
    base_url = context.config_manager.get_base_url()

    if request.method == 'POST':
        # Delegate to the POST handler
        return handle_post_request(request, headers, base_url, csrf_token)

    # Fetch all contracts with prepopulated transact_data
    raw_contracts = fetch_all_contracts(request, headers, base_url, csrf_token)
    default_contract_type = context.domain_manager.get_default_contract_type()

    contracts = [
        {
            "contract_type": contract["contract_type"],
            "contract_idx": contract["contract_idx"],
            "contract_name": contract["contract_name"],
            "transact_logic": contract.get("transact_logic", {}),
            "pre_transact_data": {var: 0 for var in extract_transaction_variables(contract.get("transact_logic"))} 

        }
        
        for contract in raw_contracts
    ]

    contract_types = sorted(set(contract["contract_type"] for contract in contracts))

    # Initialize the form with contract data
    transaction_form = TransactionForm(contracts=contracts)

    form_context = {
        "contracts": contracts,
        "contract_types": contract_types,
        "default_contract_type": context.domain_manager.get_default_contract_type(),
        "transaction_form":transaction_form
    }
    if extra_context:
        form_context.update(extra_context)

    return render(request, "admin/add_transaction.html", form_context)