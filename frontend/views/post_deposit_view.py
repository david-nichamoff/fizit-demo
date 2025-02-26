import logging
import json
import requests

from datetime import datetime
from django.contrib import messages
from django.shortcuts import render, redirect

from api.config import ConfigManager
from api.secrets import SecretsManager
from api.registry import RegistryManager
from api.operations import BankOperations, ContractOperations, SettlementOperations, CsrfOperations
from api.utilities.logging import log_info, log_warning, log_error

from frontend.forms import PostDepositForm

logger = logging.getLogger(__name__)

# Initialize API connections
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

# Fetch contracts for dropdown selection
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

# Fetch all settlements where `settle_pay_dt` is null
def fetch_all_settlements(request, headers, base_url, csrf_token, contracts):
    try:
        settlement_ops = SettlementOperations(headers, base_url, csrf_token)
        settlements = {}

        for contract in contracts:
            contract_type = contract["contract_type"]
            contract_idx = contract["contract_idx"]

            try:
                raw_settlements = settlement_ops.get_settlements(contract_type, contract_idx)
                filtered_settlements = [
                    {"settle_idx": s["settle_idx"], "settle_due_dt": s["settle_due_dt"]}
                    for s in raw_settlements if s.get("settle_pay_dt") is None
                ]

                # Use the "sale_1" format 
                key = f"{contract_type}_{contract_idx}"
                settlements[key] = filtered_settlements

            except Exception as e:
                log_error(logger, f"Error fetching settlements for {contract_type} - {contract_idx}: {e}")

        return settlements

    except Exception as e:
        log_error(logger, f"Failed to fetch settlements: {e}")
        return {}

# Handle POST deposit submission
def handle_post_deposit(request, headers, base_url, csrf_token, context):

    contracts = context["contracts"]
    settlements = json.loads(context["settlements"]) if isinstance(context["settlements"], str) else context["settlements"]

    form = PostDepositForm(request.POST, contracts=contracts, settlements=settlements)

    if not form.is_valid():
        messages.error(request, "Invalid form submission.")
        log_error(logger, f"Form error {form.errors}")
        return redirect(request.path)

    # Extract validated data
    contract_idx = form.cleaned_data["contract_idx"]
    contract_type = form.cleaned_data["contract_type"]
    settle_idx = form.cleaned_data["settle_idx"]
    dispute_reason = form.cleaned_data["dispute_reason"]
    tx_hash = form.cleaned_data["tx_hash"]
    deposit_amt = form.cleaned_data["deposit_amt"]
    deposit_dt = form.cleaned_data["deposit_dt"]

    deposit_payload = {
        "settle_idx": settle_idx,
        "dispute_reason": dispute_reason or "",
        "tx_hash": tx_hash,
        "deposit_amt": float(deposit_amt),
        "deposit_dt": deposit_dt.isoformat(),
    }

    log_info(logger, f"Posting deposit: {deposit_payload}")
    bank_ops = BankOperations(headers, base_url, csrf_token)

    response = bank_ops.post_deposit(contract_type, contract_idx, deposit_payload)

    if response.get("count", 0) > 0:
        messages.success(request, "Deposit posted successfully.")
    else:
        messages.error(request, "Failed to post deposit.")

    return redirect(request.path)


# Main view
def post_deposit_view(request, extra_context=None):
    headers, registry_manager, config_manager, csrf_token = initialize_backend_services()
    base_url = config_manager.get_base_url()

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

    log_info(logger, f"Fetched contracts: {contracts}")

    # Fetch settlements where `settle_pay_dt` is null
    settlements = fetch_all_settlements(request, headers, base_url, csrf_token, contracts)

    # Initialize form and variables
    post_deposit_form = PostDepositForm(contracts=contracts, initial={
        "deposit_dt": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
    })

    contract_types = sorted(set(contract["contract_type"] for contract in contracts))

    context = {
        "contracts": contracts,
        "contract_types": contract_types,
        "default_contract_type": registry_manager.get_default_contract_type(),
        "settlements": json.dumps(settlements),
        "post_deposit_form": post_deposit_form
    }

    log_info(logger, f"Context for rendering: {context}")

    if request.method == 'POST':
        return handle_post_deposit(request, headers, base_url, csrf_token, context)

    if extra_context:
        context.update(extra_context)

    return render(request, "admin/post_deposit.html", context)