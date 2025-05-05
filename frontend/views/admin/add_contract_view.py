import logging
import requests

from django.shortcuts import render, redirect
from django.contrib import messages

from api.operations import ContractOperations, BankOperations, CsrfOperations
from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_info, log_warning, log_error

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

def fetch_bank_data(headers, context, csrf_token  ):

    bank_ops = BankOperations(headers, context.config_manager.get_base_url(), csrf_token)

    accounts = []
    recipients = []

    for bank in context.domain_manager.get_banks():
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
def fetch_contract_templates(headers, context):

    contract_types = context.domain_manager.get_contract_types()
    all_templates = []

    for contract_type in contract_types:
        try:
            templates = context.library_manager.get_templates_by_contract_type(contract_type)
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
    headers, context, csrf_token = initialize_backend_services()
    logger.info(f"Request method: {request.method}")
    logger.info(f"request.GET: {request.GET}")
    logger.info(f"request.POST: {request.POST}")

    # Extract contract_type from GET or POST
    contract_type = request.GET.get("contract_type") or request.POST.get("contract_type")
    log_info(logger, f"Selected contract_type: {contract_type}")

    # Fetch accounts, recipients, and templates
    accounts, recipients = fetch_bank_data(headers, context, csrf_token)
    templates = fetch_contract_templates(headers, context)
    log_info(logger, f"Templates received: {templates}")

    # Prepare account and recipient choices
    account_choices = [(account['id'], account['name']) for account in accounts]
    recipient_choices = [(recipient['id'], recipient['name']) for recipient in recipients]

    # Retrieve the correct contract form and template from the registry
    contract_form_class = context.form_manager.get_contract_form(contract_type)
    log_info(logger, "Contract form retrieved")
    contract_template = context.domain_manager.get_contract_template(contract_type)
    log_info(logger, "Contract template retrieved")

    banks = context.domain_manager.get_banks()

    token_config = context.config_manager.get_all_token_addresses()
    token_list = []
    for entry in token_config:
        network = entry["key"]
        for token in entry.get("value", []):
            symbol = token["key"]
            token_list.append(f"{network}:{symbol}")

    if request.method == 'POST':
        contract_form = contract_form_class(request.POST, banks=banks, token_list=token_list)
        log_info(logger, f"Populating accounts: {account_choices}, recipients: {recipient_choices}")

        if context.api_manager.get_advance_api(contract_type) or context.api_manager.get_distribution_api(contract_type):
            contract_form.fields['funding_account'].choices = account_choices
            contract_form.fields['funding_recipient'].choices = recipient_choices

        if context.api_manager.get_deposit_api(contract_type):
            contract_form.fields['deposit_account'].choices = account_choices

        if contract_form.is_valid():
            return handle_post_request(request, headers, context, contract_type, csrf_token, contract_form)
        else:
            log_error(logger, f"Contract form errors: {contract_form.errors}")
    
    contract_form = contract_form_class(banks=banks, token_list=token_list)

    # Prepare form_context for rendering
    form_context = {
        'contract_type': contract_type,
        'contract_form': contract_form,
        'accounts': accounts,
        'recipients': recipients,
        'templates': templates,
        **(extra_context or {}),
    }

    return render(request, contract_template, form_context)

# Handle POST request
def handle_post_request(request, headers, context, contract_type, csrf_token, contract_form):
    contract_data = contract_form.cleaned_data
    log_info(logger, f"contract_data: {contract_data}")

    if contract_data.get("funding_method") is not None:
        contract_data["funding_instr"] = context.domain_manager.generate_instruction_data("funding",
            bank=contract_data.get("funding_method"),
            funding_account=contract_data.get("funding_account"),
            funding_recipient=contract_data.get("funding_recipient"),
            funding_token_symbol=contract_data.get("funding_token_symbol"),
            funding_token_network=contract_data.get("funding_token_network"),
            advance_amt=contract_data.get("advance_amt"),
            residual_calc_amt=contract_data.get("residual_calc_amt")
        )

        log_info(logger, f"Funding instructions: {contract_data["funding_instr"]}")

    if contract_data.get("deposit_method") is not None:
        contract_data["deposit_instr"] = context.domain_manager.generate_instruction_data("deposit",
            bank=contract_data.get("deposit_method"),
            deposit_account=contract_data.get("deposit_account"),
            deposit_token_network=contract_data.get("deposit_token_network"),
            deposit_token_symbol=contract_data.get("deposit_token_symbol"),
            distribution_calc_amt=contract_data.get("distribution_calc_amt")
        )

        log_info(logger, f"Deposit instructions: {contract_data["deposit_instr"]}")

    # Add additional data for the contract
    contract_data.update({
        "service_fee_max": contract_data.get("service_fee_pct", 0.025),
        "extended_data": {},
        "is_active": True,
        "is_quote": False,
    })

    # Submit contract data
    try:
        base_url = context.config_manager.get_base_url()
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