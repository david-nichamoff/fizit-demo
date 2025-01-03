from django.shortcuts import render, redirect
from django.contrib import messages
from api.managers import ConfigManager, SecretsManager
from api.operations import TransactionOperations, ContractOperations
from frontend.forms import TransactionForm

from datetime import datetime

import json
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
def fetch_all_contracts(headers, config):

    contract_ops = ContractOperations(headers, config)

    try:
        count_response = contract_ops.get_count()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch contract count: {e}")
        return []

    contract_count = count_response.json()['contract_count']
    logger.info(f"contract_count: {contract_count}")

    # Fetch contracts one by one
    contracts = []
    for contract_idx in range(0, contract_count):
        try:
            contract_response = contract_ops.get_contract(contract_idx)
            contract_response.raise_for_status()
            contract = contract_response.json()

            # Extract and process transact_logic
            transact_logic = contract.get("transact_logic", {})
            variables = extract_transaction_variables(transact_logic)
            contract["pre_transact_data"] = {var: 0 for var in variables}

            contracts.append(contract)
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch contract {contract_idx}: {e}")

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
def handle_post_request(request, headers, config):
    contract_idx = request.POST.get("contract_idx")
    transact_dt = request.POST.get("transact_dt")
    transact_data_raw = request.POST.get("transact_data")

    if not contract_idx or not transact_dt or not transact_data_raw:
        messages.error(request, "All fields are required.")
        return redirect(request.path)

    try:
        # Parse transact_data from JSON
        transact_data = json.loads(transact_data_raw)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in transact_data: {e}")
        messages.error(request, "Invalid JSON in Transaction Data. Please correct it and try again.")
        return redirect(request.path)

    try:
        # Use TransactionOperations to post the transaction
        transaction_data = [{
            "extended_data": {},
            "transact_dt": transact_dt,
            "transact_data": transact_data,
        }]
        transaction_ops = TransactionOperations(headers, config)
        response = transaction_ops.post_transactions(contract_idx, transaction_data)

        # Check for response status
        if response.status_code == 200 or response.status_code == 201:
            messages.success(request, "Transaction added successfully.")
            return redirect(request.path)
        else:
            # Log the error details from the response
            logger.error(f"Failed to add transaction: {response.json()}")
            messages.error(request, f"Failed to add transaction: {response.json()}")
            return redirect(request.path)

    except requests.RequestException as e:
        logger.error(f"Failed to add transaction: {e}")
        messages.error(request, "Failed to add transaction due to a network error.")
        return redirect(request.path)

# Main view
def add_transaction_view(request, extra_context=None):
    headers, config = initialize_backend_services()

    if request.method == 'POST':
        # Delegate to the POST handler
        return handle_post_request(request, headers, config)

    # Fetch all contracts with prepopulated transact_data
    raw_contracts = fetch_all_contracts(headers, config)

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
    transaction_form = TransactionForm(contracts=contracts)

    context = {
        "transaction_form": transaction_form,
        "contracts": contracts,
        "current_datetime": datetime.now().isoformat(),
    }
    if extra_context:
        context.update(extra_context)

    return render(request, "admin/add_transaction.html", context)