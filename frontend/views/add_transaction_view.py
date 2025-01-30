
import json
import requests
import logging

from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib import messages

from api.config import ConfigManager
from api.secrets import SecretsManager
from api.operations import TransactionOperations, ContractOperations, CsrfOperations
from api.utilities.logging import log_info, log_warning, log_error

from frontend.forms import TransactionForm

logger = logging.getLogger(__name__)

# Helper function to initialize headers and configuration
def initialize_backend_services():
    secrets_manager = SecretsManager()
    config_manager = ConfigManager()
    headers = {
        'Authorization': f"Api-Key {keys['FIZIT_MASTER_KEY']}",
        'Content-Type': 'application/json',
    }
    csrf_ops = CsrfOperations(headers, config)
    csrf_token = csrf_ops.get_csrf_token()

    return headers, config, csrf_token

# Fetch total contract count and fetch each contract one by one
def fetch_all_contracts(request, headers, config):

    contract_ops = ContractOperations(headers, config)

    try:
        response = contract_ops.get_count()
    except Exception as e:
        error_message = f"Failed to get contract count"
        log_error(logger, f"{error_message}: {e}")
        messages.error(request, f"{error_message}")

    contract_count = response.get("count")
    log_info(logger, f"contract_count: {contract_count}")

    # Fetch contracts one by one
    contracts = []
    for contract_idx in range(0, contract_count):
        try:
            contract = contract_ops.get_contract(contract_idx)

            # Extract and process transact_logic
            transact_logic = contract.get("transact_logic", {})
            log_info(logger, f"Transact Logic: {transact_logic}")

            variables = extract_transaction_variables(transact_logic)
            log_info(logger, f"Variables: {variables}")

            contract["pre_transact_data"] = {var: 0 for var in variables}
            log_info(logger, f"Contract: {contract}")

            contracts.append(contract)

        except Exception as e:
            error_message = f"Failed to fech contract {contract_idx}"
            log_warning(logger, f"{error_message}")
            messages.warning(request, f"{error_message}")

    return contracts

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
    transact_dt = request.POST.get("transact_dt")
    transact_data_raw = request.POST.get("transact_data")

    if not contract_idx or not transact_dt or not transact_data_raw:
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
        transaction_ops = TransactionOperations(headers, config, csrf_token)
        response = transaction_ops.post_transactions(contract_idx, transaction_data)

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
    headers, config, csrf_token = initialize_backend_services()

    if request.method == 'POST':
        # Delegate to the POST handler
        return handle_post_request(request, headers, config, csrf_token)

    # Fetch all contracts with prepopulated transact_data
    raw_contracts = fetch_all_contracts(request, headers, config)

    contracts = [
        {
            "contract_idx": contract["contract_idx"],
            "contract_name": contract["contract_name"],
            "transact_logic": contract.get("transact_logic", {}),
            "pre_transact_data": contract.get("pre_transact_data", {})
        }

        for contract in raw_contracts
    ]

    # Initialize the form with contract data
    log_info(logger, f"Calling transaction form with data {contracts}")
    transaction_form = TransactionForm(contracts=contracts)

    context = {
        "transaction_form": transaction_form,
        "contracts": contracts,
        "current_datetime": datetime.now().isoformat(),
    }
    if extra_context:
        context.update(extra_context)

    return render(request, "admin/add_transaction.html", context)