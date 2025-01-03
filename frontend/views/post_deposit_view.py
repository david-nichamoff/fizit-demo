import logging
import requests

from django.contrib import messages
from django.shortcuts import render, redirect

from api.managers import ConfigManager, SecretsManager
from api.operations import BankOperations, CsrfOperations, SettlementOperations
from frontend.forms import PostDepositForm

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

# Helper function to handle deposit posting
def handle_post_deposit(form, headers, config, request):
    """
    Handles the logic for posting a deposit to the backend API.
    """
    contract_idx = form.cleaned_data["contract_idx"]
    deposit_dt = form.cleaned_data["deposit_dt"]
    deposit_amt = form.cleaned_data["deposit_amt"]
    settle_idx = form.cleaned_data["settle_idx"]
    dispute_reason = form.cleaned_data["dispute_reason"]

    logger.info(f"Posting deposit for Contract IDX: {contract_idx}")

    # Prepare payload
    deposit_to_post = {
        "deposit_dt": deposit_dt,
        "deposit_amt": deposit_amt,
        "settle_idx": settle_idx,
        "dispute_reason": dispute_reason,
    }

    bank_ops = BankOperations(headers, config)
    csrf_ops = CsrfOperations(headers, config)

    csrf_token = csrf_ops.get_csrf_token()

    deposit_response = bank_ops.add_deposits(contract_idx, deposit_to_post, csrf_token)

    if deposit_response.status_code == 201:
        messages.success(request, "Deposit posted successfully.")
        return True
    else:
        logger.error(f"Failed to post deposit: {deposit_response.json()}")
        messages.error(request, f"Failed to post deposit: {deposit_response.json().get('error', 'Unknown error')}")
        return False

def fetch_settlements(headers, config, contract_idx):
    """
    Fetches settlements for the given contract index from the backend API.
    """

    settlement_ops = SettlementOperations(headers, config)

    try:
        settlement_response = settlement_ops.get_settlements(contract_idx)
        if settlement_response.status_code == 200:
            return settlement_response.json()  # Return settlements as a list
        else:
            logger.error(f"Failed to fetch settlements: {settlement_response.json()}")
            return []
    except Exception as e:
        logger.error(f"Exception while fetching settlements: {e}")
        return []

def post_deposit_view(request, extra_context=None):
    headers, config = initialize_backend_services()

    # Retrieve deposits and contract index from session
    deposits = request.session.get('deposits', [])
    selected_contract_idx = request.session.get('selected_contract_idx', None)
    settlements = []

    logger.info(f"deposits: {deposits}")
    logger.info(f"selected_contract_idx: {selected_contract_idx}")

    if selected_contract_idx:
        # Fetch settlements for the selected contract
        settlements = fetch_settlements(headers, config, selected_contract_idx)

    if request.method == 'POST' and "post_deposit" in request.POST:
        form = PostDepositForm(request.POST)
        if form.is_valid():
            # Process deposit posting
            return handle_post_deposit(request, headers, config)

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