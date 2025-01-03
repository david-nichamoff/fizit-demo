import logging
import requests

from django.shortcuts import render, redirect
from django.contrib import messages

from api.managers import ConfigManager, LibraryManager, SecretsManager
from api.operations import ContractOperations, BankOperations
from frontend.forms import ContractForm

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

# Helper function to generate instruction data
def generate_instruction_data(method, token_symbol=None, account_id=None, recipient_id=None):
    if method == 'token':
        return {"bank": "token", "token_symbol": token_symbol}
    elif method == 'mercury':
        data = {"bank": "mercury", "account_id": account_id}
        if recipient_id:
            data["recipient_id"] = recipient_id
        return data
    return {}

# Helper function to fetch accounts and recipients
def fetch_bank_data(headers, config):

    bank_ops = BankOperations(headers, config)
    accounts_response = bank_ops.get_accounts(bank='mercury')
    recipients_response = bank_ops.get_recipients(bank='mercury')

    accounts = process_bank_data(accounts_response.json(), 'account_id', 'account_name')
    recipients = process_bank_data(recipients_response.json(), 'recipient_id', 'recipient_name')

    return accounts, recipients

# Centralized API fetch logic
def process_bank_data(items, item_id_key, item_name_key):
    try:
        return [
            {'id': item[item_id_key], 'name': item[item_name_key]}
            for item in items if item_id_key in item and item_name_key in item
        ]
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to process data: {e}")
        return []

# Fetch templates for contract types and transaction logic
def fetch_contract_templates(headers, config):

    library_manager = LibraryManager()
    contract_types = config.get("contract_type", [])
    all_templates = []

    for contract_type in contract_types:
        try:
            templates = library_manager.get_logics_by_contract_type(contract_type)
            all_templates.extend({
                'contract_type': contract_type,
                'logics': template.get('transact_logic'),
                'description': template.get('description', 'No description available'),
            } for template in templates)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching templates for {contract_type}: {e}")
    return all_templates

# Main view
def add_contract_view(request, extra_context=None):
    headers, config = initialize_backend_services()

    # Fetch accounts, recipients, and templates
    accounts, recipients = fetch_bank_data(headers, config)
    templates = fetch_contract_templates(headers, config)

    # Prepare account and recipient choices
    account_choices = [(account['id'], account['name']) for account in accounts]
    recipient_choices = [(recipient['id'], recipient['name']) for recipient in recipients]

    # Initialize form for POST or GET
    if request.method == 'POST':
        contract_form = ContractForm(request.POST)
    else:
        contract_form = ContractForm()

    # Set dynamic choices explicitly
    contract_form.fields['funding_account'].choices = account_choices
    contract_form.fields['deposit_account'].choices = account_choices
    contract_form.fields['funding_recipient'].choices = recipient_choices

    if request.method == 'POST' and contract_form.is_valid():
        return handle_post_request(request, headers, config, contract_form)

    # Prepare context for rendering
    context = {
        'contract_form': contract_form,
        'accounts': accounts,
        'recipients': recipients,
        'templates': templates,
        **(extra_context or {}),
    }

    return render(request, 'admin/add_contract.html', context)

# Handle POST request
def handle_post_request(request, headers, config, contract_form):
    logger.info(f"Contract form errors:  {contract_form.errors}")

    contract_data = contract_form.cleaned_data

    logger.info(f"contract_data: {contract_data}")

    # Generate funding and deposit instructions
    contract_data["funding_instr"] = generate_instruction_data(
    method=contract_data.get("funding_method"),
            token_symbol=contract_data.get("funding_token_symbol"),
            account_id=contract_data.get("funding_account"),
            recipient_id=contract_data.get("funding_recipient")
    )

    contract_data["deposit_instr"] = generate_instruction_data(
        method=contract_data.get("deposit_method"),
        token_symbol=contract_data.get("deposit_token_symbol"),
        account_id=contract_data.get("deposit_account")
    )

    # Add additional data for the contract
    contract_data.update({
        "service_fee_max": contract_data.get("service_fee_pct", 0.025),
        "notes": "Default notes",
        "extended_data": {},
        "is_active": True,
        "is_quote": False,
    })

    # Submit contract data
    try:
        response = ContractOperations(headers, config).load_contract(contract_data)
        response.raise_for_status()
        contract_idx = response.json()
        messages.success(request, f"Contract {contract_idx} added successfully!")
        return redirect(f"/admin/view-contract/?contract_idx={contract_idx}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Contract submission failed: {e}")
        messages.error(request, "Failed to add contract. Please try again.")

    return redirect(request.path)