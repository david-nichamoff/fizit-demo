import requests
import logging
import json
from django.contrib import messages
from api.managers import ConfigManager, SecretsManager
from api.operations import BankOperations, ContractOperations, SettlementOperations
from frontend.forms import PostDepositForm, FindDepositsForm
from django.shortcuts import render, redirect
from datetime import datetime, timedelta

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

# Fetch all contracts
def fetch_all_contracts(headers, config):
    base_url = config["url"]
    operations = ContractOperations(headers, config)

    count_url = f"{base_url}/api/contracts/count/"
    try:
        count_response = requests.get(count_url, headers=headers)
        count_response.raise_for_status()
        contract_count = count_response.json()['contract_count']
    except requests.RequestException as e:
        logger.error(f"Failed to fetch contract count: {e}")
        return []

    contracts = []
    for contract_idx in range(contract_count):
        try:
            response = operations.get_contract(contract_idx)
            response.raise_for_status()
            contracts.append(response.json())
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch contract {contract_idx}: {e}")

    return contracts

def fetch_deposits(headers, config, contract_idx, start_date, end_date):
    operations = BankOperations(headers, config)

    try:
        # Use the get_deposits method from BankOperations
        response = operations.get_deposits(contract_idx, start_date, end_date)
        
        # Ensure the response is parsed correctly
        if response.status_code == 200:
            return response.json()  # Extract JSON data from response
        else:
            logger.error(f"Failed to fetch deposits for contract {contract_idx}: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Failed to fetch deposits for contract {contract_idx}: {e}")
        return []

def handle_post_deposit(request, headers, config):
    form = PostDepositForm(request.POST)
    if form.is_valid():
        contract_idx = form.cleaned_data["contract_idx"]
        deposit_dt = form.cleaned_data["deposit_dt"]
        deposit_amt = form.cleaned_data["deposit_amt"]
        settle_idx = form.cleaned_data["settle_idx"]
        dispute_reason = form.cleaned_data["dispute_reason"]

        logger.info(f"Contract IDX to post: {contract_idx}")
        logger.info(f"Deposit Date: {deposit_dt}, Amount: {deposit_amt}")
        logger.info(f"Settlement IDX: {settle_idx}, Dispute Reason: {dispute_reason}")

        # Prepare payload
        data_to_post = {
            "deposit_dt": deposit_dt,
            "deposit_amt": deposit_amt,
            "settle_idx": settle_idx,
            "dispute_reason": dispute_reason,
        }

        base_url = config["url"]
        post_url = f"{base_url}/api/contracts/{contract_idx}/deposits/"
        response = requests.post(post_url, headers=headers, json=data_to_post)

        if response.status_code == 201:
            messages.success(request, "Deposit posted successfully.")
        else:
            logger.error(f"Failed to post deposit: {response.json()}")
            messages.error(request, f"Failed to post deposit: {response.json().get('error', 'Unknown error')}")

    else:
        logger.error("Invalid form data for posting deposit.")
        messages.error(request, "Invalid form data submitted.")

    return redirect(request.path)

def handle_find_deposits(request, headers, config, contracts):
    """
    Handle the process of finding deposits.
    """
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

        logger.info(f"Deposits found: {deposits}")

        # Set success or no deposits message
        if deposits:
            messages.success(request, "Deposits fetched successfully.")
        else:
            messages.success(request, "No deposits found for this contract.")
    else:
        messages.error(request, "Invalid data for finding deposits.")

    return find_deposits_form, deposits, selected_contract_idx

def add_deposit_view(request, extra_context=None):
    headers, config = initialize_backend_services()

    deposits = []
    settlements = []

    selected_contract_idx = None

    # Fetch contracts for dropdown
    raw_contracts = fetch_all_contracts(headers, config)
    contracts = [{"contract_idx": c["contract_idx"], "contract_name": c["contract_name"]} for c in raw_contracts]

    # Initialize forms
    find_deposits_form = FindDepositsForm(contracts=contracts, initial={
        "start_date": (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%dT%H:%M:%S'),
        "end_date": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
    })

    post_deposit_form = PostDepositForm()

    if request.method == 'POST':
        if "find_deposits" in request.POST:
            find_deposits_form, deposits, selected_contract_idx = handle_find_deposits(
                request, headers, config, contracts
            )

            # Fetch the selected contract name
            selected_contract = next((c for c in contracts if c["contract_idx"] == int(selected_contract_idx)), {})

            operations = SettlementOperations(headers, config)
            response = operations.get_settlements(selected_contract_idx)
            settlements = response.json()

            post_deposit_form = PostDepositForm(initial={
                "contract_idx": selected_contract_idx,
                "contract_name": selected_contract.get("contract_name", ""),
            })
    
        elif "post_deposit" in request.POST:
            return handle_post_deposit(request, headers, config)

    logger.info(f"deposits passed to template: {deposits}")

    # Prepare context
    context = {
        "find_deposits_form": find_deposits_form,
        "post_deposit_form": post_deposit_form,
        "contracts": contracts,
        "deposits": deposits,
        "settlements": settlements,
        "selected_contract_idx": selected_contract_idx,
    }

    if extra_context:
        context.update(extra_context)

    return render(request, "admin/add_deposit.html", context)