import logging
import json
from json_logic import jsonLogic

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings

from api.operations import ContractOperations, SettlementOperations, TransactionOperations, BankOperations
from api.operations import CsrfOperations, PartyOperations, ArtifactOperations
from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_info, log_warning, log_error
from api.utilities.report import generate_contract_report
from api.utilities.logic import extract_transaction_variables
from api.models import ContractAuxiliary

from frontend.forms.common import PartyForm, ArtifactForm

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

# Main view
@login_required(login_url='/dashboard/login/')
def view_contract_view(request, customer, extra_context=None):
    headers, context, csrf_token = initialize_backend_services()
    contract_idx = request.GET.get("contract_idx")
    contract_type = request.GET.get("contract_type")

    log_info(logger, f"Fetching {contract_type}:{contract_idx} for customer {customer}")

    if not contract_idx:
        messages.error(request, "Missing contract index.")
        return redirect("list_contracts", customer=customer)

    if not contract_type:
        messages.error(request, "Missing contract type.")
        return redirect("list_contracts", customer=customer)

    base_url = context.config_manager.get_base_url()

    if request.method == 'POST':
        return handle_post_request(request, customer, context, contract_type, contract_idx, headers, base_url, csrf_token)

    # Prepare form_context and render the appropriate template
    form_context = prepare_view_form_context(request, customer, context, contract_type, contract_idx, headers, base_url, csrf_token, extra_context)
    return render(request, f"dashboard/view_{contract_type}_contract.html", form_context)

# Handle POST requests for different forms
def handle_post_request(request, customer, context, contract_type, contract_idx, headers, base_url, csrf_token):
    form_type = request.POST.get("form_type")

    log_info(logger, f"Handling form submission: {form_type}")

    form_handlers = {
        "artifacts": _update_artifacts,
        "generate_report": _generate_report,
        "execute_logic" : _execute_transact_logic
    }

    handler = form_handlers.get(form_type)
    log_info(logger, f"Calling {form_type} with contract {contract_idx} and contract_type {contract_type}")

    if handler:
        return handler(request, context, contract_type, contract_idx, headers, base_url, csrf_token)

    messages.error(request, "Invalid form type. Please correct the form and try again.")
    return redirect(f"/dashboard/{customer}/view-contract/?contract_idx={contract_idx}?contract_type={contract_type}")

# Prepare form_context for rendering the view
def prepare_view_form_context(request, customer, context, contract_type, contract_idx, headers, base_url, csrf_token, extra_context=None):
    contract_ops = ContractOperations(headers, base_url, csrf_token)
    bank_ops = BankOperations(headers, base_url, csrf_token)

    try:
        contract = contract_ops.get_contract(contract_type, contract_idx)
        log_info(logger, f"Returned contract {contract}")
    except Exception as e:
        log_error(logger, f"Failed to fetch {contract_type}:{contract_idx}: {e}")
        messages.error(request, f"Failed to fetch {contract_type} contract {contract_idx}")
        return {}

    # Extract fields from funding_instr
    funding_instr = contract.get("funding_instr", {})
    deposit_instr = contract.get("deposit_instr", {})

    banks = context.domain_manager.get_banks()
    contract["funding_method"] = funding_instr["bank"].capitalize()
    funding_method = funding_instr.get("bank", "")

    try:
        accounts = bank_ops.get_accounts(funding_method)
    except Exception as e:
        log_warning(logger, f"Error retrieving accounts for bank '{funding_method}': {e}")
        accounts = []

    # Gracefully map account name
    account_id = funding_instr.get("account_id")

    for account in accounts:
        if isinstance(account, dict) and account.get("account_id") == account_id:
            contract["funding_account"] = account.get("account_name")
            break

    try:
        recipients = bank_ops.get_recipients(funding_method)
    except Exception as e:
        log_warning(logger, f"Error retrieving recipients for bank '{funding_method}': {e}")
        recipients = []

    recipient_id = funding_instr.get("recipient_id")

    log_info(logger, f"Recipients: {recipients}, recipient id: {recipient_id}")

    for recipient in recipients:
        if isinstance(recipient, dict) and recipient.get("recipient_id") == recipient_id:
            contract["funding_recipient"] = recipient.get("recipient_name")
            contract["recipient_payment_method"] = recipient.get("payment_method")
            contract["recipient_account_number"] = recipient.get("account_number")
            contract["recipient_routing_number"] = recipient.get("routing_number")
            contract["recipient_bank_name"] = recipient.get("bank_name")
            contract["recipient_address_1"] = recipient.get("address_1")
            contract["recipient_address_2"] = recipient.get("address_2")
            contract["recipient_city"] = recipient.get("city")
            contract["recipient_region"] = recipient.get("region")
            contract["recipient_postal_code"] = recipient.get("postal_code")
            contract["recipient_country"] = recipient.get("country")
            break

    try:
        contract_release = context.config_manager.get_contract_release(contract_type)
        aux = ContractAuxiliary.objects.filter(
            contract_idx=contract_idx,
            contract_type=contract_type,
            contract_release=contract_release
        ).first()
        contract["transact_logic_natural"] = aux.logic_natural if aux else "No translation available."
    except Exception as e:
        log_warning(logger, f"Failed to load natural language translation: {e}")
        contract["transact_logic_natural"] = "No translation available."

    transact_logic = contract.get("transact_logic")
    logic_variables = []

    try:
        if isinstance(transact_logic, str):
            transact_logic = json.loads(transact_logic)
        logic_variables = sorted(extract_transaction_variables(transact_logic))
    except Exception as e:
        log_warning(logger, f"Failed to parse transact_logic or extract vars: {e}")

    # Fetch related data
    try:
        log_info(logger, "Fetching settlements")
        
        settlements=[]
        if context.api_manager.get_settlement_api(contract_type):
            settlements = fetch_settlements(contract_type, contract_idx, headers, base_url)

        parties = fetch_parties(contract_type, contract_idx, headers, base_url)
        transactions = fetch_transactions(contract_type, contract_idx, headers, base_url)
        artifacts = fetch_artifacts(contract_type, contract_idx, headers, base_url)

    except Exception as e:
        log_error(logger, f"Failed to fetch related data for {contract_type}:{contract_idx}: {e}")
        messages.error(request, f"Failed to fetch related data.")

    token_list = []
    token_config = context.config_manager.get_all_token_addresses()
    for entry in token_config:
        network = entry["key"]
        for token in entry.get("value", []):
            symbol = token["key"]
            token_list.append(f"{network}:{symbol}")

    contract_form_template  = context.form_manager.get_contract_form(contract_type)
    contract_form = contract_form_template(
        initial=contract, 
        banks=banks, 
        token_list=token_list,
        
        readonly_fields = [
            "transact_logic", "service_fee_pct", "service_fee_amt", 
            "funding_method", "funding_account", "funding_recipient", "funding_token_symbol"
        ],
        
        hidden_fields = [],
        percent_display=True)

    settlement_form = None
    if context.form_manager.get_settlement_form(contract_type):
        settlement_form_template = context.form_manager.get_settlement_form(contract_type)
        settlement_form = settlement_form_template(initial=contract)

    party_codes = context.config_manager.get_party_codes()
    party_types = context.domain_manager.get_party_types()

    # Prepare form_context
    form_context = {
        'contract_idx': contract_idx,
        'contract_type': contract_type,
        'contract_form': contract_form,
        'party_form': PartyForm(party_codes=party_codes, party_types=party_types),
        'settlement_form': settlement_form,
        'artifact_form': ArtifactForm(),
        'settlements': settlements,
        'parties': parties,
        'transactions': transactions,
        'artifacts': artifacts,
        'customer': customer,
        'logic_variables': logic_variables,
    }

    if extra_context:
        form_context.update(extra_context)

    return form_context

# Update artifacts
def _update_artifacts(request, context, contract_type, contract_idx, headers, base_url, csrf_token):
    artifact_url = request.POST.getlist("artifact_url")

    if not artifact_url:
        messages.error(request, "No artifact URL provided.")
        return redirect(f"/admin/view-contract/?contract_idx={contract_idx}&contract_type={contract_type}")

    artifact_ops = ArtifactOperations(headers, base_url, csrf_token)

    try:
        log_info(logger, f"Posting artifact {artifact_url}")
        response = artifact_ops.post_artifacts(contract_type, contract_idx, artifact_url)
        if response["count"] > 0:
            messages.success(request, "Artifact uploaded successfully.")
        else: 
            raise RuntimeError

    except Exception as e:
        error_message = f"Failed to add artifact"
        log_error(logger, f"{error_message}: {e}")
        messages.error(request, f"{error_message}")

    return redirect(f"/admin/view-contract/?contract_idx={contract_idx}&contract_type={contract_type}")

# Fetch related data
def fetch_parties(contract_type, contract_idx, headers, base_url):
    party_ops = PartyOperations(headers, base_url)
    return party_ops.get_parties(contract_type, contract_idx)

def fetch_settlements(contract_type, contract_idx, headers, base_url):
    settlement_ops = SettlementOperations(headers, base_url)
    return settlement_ops.get_settlements(contract_type, contract_idx)

def fetch_transactions(contract_type, contract_idx, headers, base_url):
    transaction_ops = TransactionOperations(headers, base_url)
    return transaction_ops.get_transactions(contract_type, contract_idx)

def fetch_artifacts(contract_type, contract_idx, headers, base_url):
    artifact_ops = ArtifactOperations(headers, base_url)
    return artifact_ops.get_artifacts(contract_type, contract_idx)

def _generate_report(request, context, contract_type, contract_idx, headers, base_url, csrf_token):
    try:
        contract_ops = ContractOperations(headers, base_url, csrf_token)
        party_ops = PartyOperations(headers, base_url, csrf_token)
        transact_ops = TransactionOperations(headers, base_url, csrf_token)
        artifact_ops = ArtifactOperations(headers, base_url, csrf_token)
        settlement_ops = SettlementOperations(headers, base_url, csrf_token)

        contract = contract_ops.get_contract(contract_type, contract_idx)
        parties = party_ops.get_parties(contract_type, contract_idx)
        transactions = transact_ops.get_transactions(contract_type, contract_idx)
        artifacts = artifact_ops.get_artifacts(contract_type, contract_idx)

        settlements = []
        if context.api_manager.get_settlement_api(contract_type):
            settlements = settlement_ops(contract_type, contract_idx)

        pdf = generate_contract_report(
            contract, parties, transactions, artifacts, settlements,
            contract_idx, contract_type,
            logo_relative_path='frontend/static/assets/logo/fizit_full_color.png',
            template_name='reports/contract_report.html'
        )

        # Return response as download
        contract_name = contract.get("contract_name")
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{contract_name}.pdf"'
        return response

    except Exception as e:
        log_error(logger, f"Failed to generate report for {contract_type}:{contract_idx}: {e}")
        messages.error(request, "Failed to generate report.")
        return redirect(f"/admin/view-contract/?contract_idx={contract_idx}&contract_type={contract_type}")

def _execute_transact_logic(request, context, contract_type, contract_idx, headers, base_url, csrf_token):
    contract_ops = ContractOperations(headers, base_url, csrf_token)
    try:
        contract = contract_ops.get_contract(contract_type, contract_idx)
        transact_logic = contract.get("transact_logic")

        if isinstance(transact_logic, str):
            transact_logic = json.loads(transact_logic)

        input_data = {}
        logic_input_values = {}

        for k, v in request.POST.items():
            if k.startswith("var_"):
                logic_input_values[k] = v
                input_data[k.replace("var_", "")] = try_cast(v)

        result = jsonLogic(transact_logic, input_data)
        log_info(logger, f"Logic_input_values: {logic_input_values}")

        extra_context = {
            "logic_input_values": logic_input_values,
            "logic_result": format_logic_result(input_data, result)
        }

        return render(
            request,
            f"dashboard/view_{contract_type}_contract.html",
            prepare_view_form_context(
                request,
                request.resolver_match.kwargs["customer"],
                context,
                contract_type,
                contract_idx,
                headers,
                base_url,
                csrf_token,
                extra_context=extra_context,
            )
        )

    except Exception as e:
        log_error(logger, f"Error executing transaction logic: {e}")
        messages.error(request, "Failed to execute transaction logic.")
        return redirect(f"/dashboard/{request.resolver_match.kwargs['customer']}/view-contract/?contract_idx={contract_idx}&contract_type={contract_type}")

def try_cast(value):
    try:
        return float(value)
    except:
        return value

def format_logic_result(input_data, result):
    lines = [f"{key}: {value}" for key, value in input_data.items()]
    lines.append(f"\nResult: {result}")
    return "\n".join(lines)
