import logging
import requests

from datetime import datetime

from django.contrib import messages
from django.shortcuts import render, redirect

from api.config import ConfigManager
from api.secrets import SecretsManager
from api.operations import BankOperations, CsrfOperations, SettlementOperations
from api.utilities.logging import log_info, log_warning, log_error

from frontend.forms import PostDepositForm

logger = logging.getLogger(__name__)

# Helper function to initialize headers and configuration
def initialize_backend_services():
    secrets_manager = SecretsManager()
    config_manager = ConfigManager()
    headers = {
        'Authorization': f"Api-Key {keys['FIZIT_MASTER_KEY']}",
        'Content-Type': 'application/json',
    }
    return headers, config

# Helper function to handle deposit posting
def handle_post_deposit(form, request, headers, config):
    """
    Handles the logic for posting a deposit to the backend API.
    """
    contract_idx = form.cleaned_data["contract_idx"]
    deposit_dt = form.cleaned_data["deposit_dt"]
    deposit_amt = float(form.cleaned_data["deposit_amt"])
    settle_idx = form.cleaned_data["settle_idx"]
    dispute_reason = form.cleaned_data["dispute_reason"]

    # Prepare payload
    deposit_to_post = {
        "deposit_dt": deposit_dt.isoformat(),
        "deposit_amt": deposit_amt,
        "settle_idx": settle_idx,
        "dispute_reason": dispute_reason,
    }

    log_info(logger, f"Posting {deposit_to_post} deposit for Contract IDX: {contract_idx}")

    csrf_ops = CsrfOperations(headers, config)
    csrf_token = csrf_ops.get_csrf_token()

    bank_ops = BankOperations(headers, config, csrf_token)
    deposit = bank_ops.post_deposit(contract_idx, deposit_to_post)

    log_info(logger, f"Deposited: {deposit}")

    if "error" not in deposit:
        messages.success(request, "Deposit posted successfully.")
        return redirect(f"/admin/")
    else:
        log_error(logger, f"Failed to post deposit: {deposit["error"]}")
        messages.error(request, f"Failed to post deposit: {deposit["error"]}")
        return redirect(f"/admin/")

def fetch_settlements(headers, config, contract_idx):
    """
    Fetches settlements for the given contract index from the backend API.
    """

    settlement_ops = SettlementOperations(headers, config)

    try:
        settlements = settlement_ops.get_settlements(contract_idx)
        if "error" not in settlements:
            return settlements  # Return settlements as a list
        else:
            log_error(logger, f"Failed to fetch settlements: {settlements["error"]}")
            return []
    except Exception as e:
        log_error(logger, f"Exception while fetching settlements: {e}")
        return []

def post_deposit_view(request, extra_context=None):
    headers, config = initialize_backend_services()

    # Retrieve deposits and contract index from session
    deposits = request.session.get('deposits', [])
    selected_contract_idx = request.session.get('selected_contract_idx', None)
    settlements = []

    log_info(logger, f"deposits: {deposits}")
    log_info(logger, f"selected_contract_idx: {selected_contract_idx}")

    if selected_contract_idx:
        # Fetch settlements for the selected contract
        settlements = fetch_settlements(headers, config, selected_contract_idx)

    if request.method == 'POST' and "post_deposit" in request.POST:
        form = PostDepositForm(request.POST)
        if form.is_valid():
            # Process deposit posting
            return handle_post_deposit(form, request, headers, config)
        else:
            messages.error(request, "Invalid form data submitted.")

    context = {
        "deposits": deposits,
        "settlements": settlements,
        "selected_contract_idx": selected_contract_idx,
        "post_deposit_form": PostDepositForm(),
    }

    # Merge with extra_context if provided
    if extra_context:
        context.update(extra_context)

    return render(request, "admin/post_deposit.html", context)