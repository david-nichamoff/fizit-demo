import logging
import requests

from django.shortcuts import render, redirect
from django.contrib import messages

from api.config import ConfigManager
from api.library import LibraryManager 
from api.secrets import SecretsManager
from api.registry import RegistryManager
from api.operations import ContractOperations, BankOperations, CsrfOperations
from api.utilities.logging import log_info, log_warning, log_error

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

# Helper function to generate instruction data
#def generate_instruction_data(method, token_symbol=None, account_id=None, recipient_id=None):
#    if method == 'token':
#        return {"bank": "token", "token_symbol": token_symbol}
#    elif method == 'mercury':
#        data = {"bank": "mercury", "account_id": account_id}
#        if recipient_id:
#            data["recipient_id"] = recipient_id
#        return data
#    return {}

# Helper function to fetch accounts and recipients
def fetch_bank_data(headers, config_manager, registry_manager, csrf_token  ):

    bank_ops = BankOperations(headers, config_manager.get_base_url(), csrf_token)
    accounts = []
    recipients = []

    for bank in registry_manager.get_banks():
        accounts_response = bank_ops.get_accounts(bank=bank)
        recipients_response = bank_ops.get_recipients(bank=bank)

        accounts.extend(process_bank_data(accounts_response, bank, 'account_id', 'account_name'))
        recipients.extend(process_bank_data(recipients_response, bank, 'recipient_id', 'recipient_name'))

    return accounts, recipients

# Centralized API fetch logic
def process_bank_data(items, bank, item_id_key, item_name_key):
    try:
        return [
            {'bank': bank, 'id': item[item_id_key], 'name': item[item_name_key]}
            for item in items if item_id_key in item and item_name_key in item
        ]
    except requests.exceptions.RequestException as e:
        log_error(logger, f"Failed to process data: {e}")
        return []

# Fetch templates for contract types and transaction logic
def fetch_contract_templates(headers, config_manager, registry_manager):

    library_manager = LibraryManager()
    contract_types = registry_manager.get_contract_types()
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
            log_error(logger, f"Error fetching templates for {contract_type}: {e}")
    return all_templates

# Main view
def add_contract_view(request, extra_context=None):
    headers, registry_manager, config_manager, csrf_token = initialize_backend_services()
    logger.info(f"Request method: {request.method}")
    logger.info(f"request.GET: {request.GET}")
    logger.info(f"request.POST: {request.POST}")

    # Extract contract_type from GET or POST
    contract_type = request.GET.get("contract_type") or request.POST.get("contract_type")
    log_info(logger, f"Selected contract_type: {contract_type}")

    # Fetch accounts, recipients, and templates
    accounts, recipients = fetch_bank_data(headers, config_manager, registry_manager, csrf_token)

    templates = fetch_contract_templates(headers, config_manager, registry_manager)
    log_info(logger, f"Templates received: {templates}")

    # Prepare account and recipient choices
    account_choices = [(account['id'], account['name']) for account in accounts]
    recipient_choices = [(recipient['id'], recipient['name']) for recipient in recipients]

    # Retrieve the correct contract form and template from the registry
    contract_form_class = registry_manager.get_contract_form(contract_type)
    contract_template = registry_manager.get_contract_template(contract_type)

    if request.method == 'POST':
        contract_form = contract_form_class(request.POST)

        if registry_manager.get_advance_api(contract_type) or registry_manager.get_distribution_api(contract_type):
            contract_form.fields['funding_account'].choices = account_choices
            contract_form.fields['funding_recipient'].choices = recipient_choices

        if registry_manager.get_deposit_api(contract_type):
            contract_form.fields['deposit_account'].choices = account_choices

        if contract_form.is_valid():
            return handle_post_request(request, headers, registry_manager, config_manager, contract_type, csrf_token, contract_form)
        else:
            log_error(logger, f"Contract form errors: {contract_form.errors}")

    contract_form = contract_form_class()

    # Prepare context for rendering
    context = {
        'contract_type': contract_type,
        'contract_form': contract_form,
        'accounts': accounts,
        'recipients': recipients,
        'templates': templates,
        **(extra_context or {}),
    }

    return render(request, contract_template, context)

# Handle POST request
def handle_post_request(request, headers, registry_manager, config_manager, contract_type, csrf_token, contract_form):
    contract_data = contract_form.cleaned_data
    log_info(logger, f"contract_data: {contract_data}")

    # Generate funding and deposit instructions
    #contract_data["funding_instr"] = generate_instruction_data(
    #method=contract_data.get("funding_method"),
    #        token_symbol=contract_data.get("funding_token_symbol"),
    #        account_id=contract_data.get("funding_account"),
    #        recipient_id=contract_data.get("funding_recipient")
    #)
#
#    contract_data["deposit_instr"] = generate_instruction_data(
#        method=contract_data.get("deposit_method"),
#        token_symbol=contract_data.get("deposit_token_symbol"),
#        account_id=contract_data.get("deposit_account")
#    )
#

    contract_data["funding_instr"] = registry_manager.generate_instruction_data("funding",
        bank=contract_data.get("funding_method"),
        funding_account=contract_data.get("funding_account"),
        funding_recipient=contract_data.get("funding_recipient"),
        funding_token_symbol=contract_data.get("funding_token_symbol"),
        advance_amt=contract_data.get("advance_amt"),
        residual_calc_amt=contract_data.get("residual_calc_amt")
    )

    contract_data["deposit_instr"] = registry_manager.generate_instruction_data("deposit",
        bank=contract_data.get("deposit_method"),
        deposit_account=contract_data.get("deposit_account"),
        deposit_token_symbol=contract_data.get("deposit_token_symbol"),
        distribution_calc_amt=contract_data.get("distribution_calc_amt")
    )

    # Add additional data for the contract
    contract_data.update({
        "service_fee_max": contract_data.get("service_fee_pct", 0.025),
        "extended_data": {},
        "is_active": True,
        "is_quote": False,
    })

    # Submit contract data
    try:
        base_url = config_manager.get_base_url()
        contract_ops = ContractOperations(headers, base_url, csrf_token)
        contract = contract_ops.post_contract(contract_type, contract_data)

        if "error" in contract:
            raise Exception(contract["error"])

        contract_idx = contract["contract_idx"]
        messages.success(request, f"Contract {contract_idx} added successfully!")
        return redirect(f"/admin/view-contract/?contract_idx={contract_idx}&contract_type={contract_type}")
    except Exception as e:
        log_error(logger, f"Contract submission failed: {e}")
        messages.error(request, "Failed to add contract. Please try again.")
        return redirect(f"/admin/add-contract/?contract_type={contract_type}")