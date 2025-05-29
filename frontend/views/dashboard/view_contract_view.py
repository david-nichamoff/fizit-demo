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

from frontend.forms.admin import PartyForm, ArtifactForm
from frontend.views.decorators.group import group_matches_customer

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
@group_matches_customer
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
        "execute_logic" : _execute_transact_logic,
        "approve_party" : _handle_approve_party,
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

    contract["funding_method"] = funding_instr["bank"].capitalize()
    funding_method = funding_instr.get("bank", "")

    if "bank" in deposit_instr:
        contract["deposit_method"] = deposit_instr["bank"].capitalize()
        funding_method = funding_instr.get("bank", "")

    # Set funding_token_symbol if available
    token_symbol = funding_instr.get("token_symbol")
    network = funding_instr.get("network")
    if token_symbol and network:
        contract["funding_network"] = network.capitalize()
        contract["funding_token_symbol"] = token_symbol.upper()

    # Set deposit_token_symbol if available
    token_symbol = deposit_instr.get("token_symbol")
    network = deposit_instr.get("network")
    log_info(logger, f"Deposit instructions: {deposit_instr}")
    if token_symbol and network:
        contract["deposit_network"] = network.capitalize()
        contract["deposit_token_symbol"] = token_symbol.upper()
    log_info(logger, f"Contract: {contract}")

    try:
        banks = context.domain_manager.get_banks()
    except Exception as e:
        log_error(logger, f"Error retrieving banks")
        banks = []

    try:
        accounts = bank_ops.get_accounts(funding_method)
    except Exception as e:
        log_error(logger, f"Error retrieving accounts for bank '{funding_method}': {e}")
        accounts = []

    # Build a lookup dictionary for account_id -> account_name
    account_lookup = {
        account.get("account_id"): account.get("account_name")
        for account in accounts if isinstance(account, dict)
    }

    # Assign funding_account and deposit_account using lookup
    contract["funding_account"] = account_lookup.get(funding_instr.get("account_id"))
    contract["deposit_account"] = account_lookup.get(deposit_instr.get("account_id"))

    try:
        recipients = bank_ops.get_recipients(funding_method)
    except Exception as e:
        log_warning(logger, f"Error retrieving recipients for bank '{funding_method}': {e}")
        recipients = []

    recipient_id = funding_instr.get("recipient_id")

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

    transactions, settlements, parties, artifacts = [], [], [], []

    # Fetch related data
    try:
        log_info(logger, "Fetching settlements")
        if context.api_manager.get_settlement_api(contract_type):
            settlements = fetch_settlements(contract_type, contract_idx, headers, base_url)

        parties = fetch_parties(contract_type, contract_idx, headers, base_url)

        for party in parties:
            party["approved"] = bool(party.get("approved_dt"))

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

    log_info(logger, f"Passing to contract form: {contract}")

    contract_form_template  = context.form_manager.get_contract_form(contract_type)
    contract_form = contract_form_template(
        initial=contract, 
        banks=banks, 
        token_list=token_list,
        
        readonly_fields = [
            "transact_logic", "service_fee_pct", "service_fee_amt", 
            "funding_method", "funding_account", "funding_recipient", "funding_token_symbol", "funding_network",
            "deposit_method", "deposit_account", "deposit_token_symbol", "deposit_network"
        ],
        
        hidden_fields = [],
        percent_display=True)

    settlement_form = None
    if context.form_manager.get_settlement_form(contract_type):
        settlement_form_template = context.form_manager.get_settlement_form(contract_type)
        settlement_form = settlement_form_template(initial=contract)

    for name, field in contract_form.fields.items():
        log_info(logger, f"FIELD: {name} | VALUE: {contract_form.initial.get(name)}")

    # Prepare form_context
    form_context = {
        'contract_idx': contract_idx,
        'contract_type': contract_type,
        'contract_release': contract_release,
        'contract_form': contract_form,
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

def _handle_approve_party(request, context, contract_type, contract_idx, headers, base_url, csrf_token):
    party_idx = request.POST.get("party_idx")
    approved_user = request.user.username  # or request.user.get_full_name() if preferred

    if not party_idx:
        messages.error(request, "Missing party ID for approval.")
        return redirect(f"/dashboard/{request.resolver_match.kwargs['customer']}/view-contract/?contract_idx={contract_idx}&contract_type={contract_type}")

    party_ops = PartyOperations(headers, base_url, csrf_token)

    try:
        log_info(logger, f"Approving party {party_idx} on {contract_type}:{contract_idx} by {approved_user}")
        result = party_ops.approve_party(contract_type, contract_idx, party_idx, approved_user)
        if "contract_idx" in result and "party_idx" in result:
            messages.success(request, f"Contract approved.")
        else:
            messages.error(request, f"Approval failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        log_error(logger, f"Approval error: {e}")
        messages.error(request, f"Failed to approve party: {e}")

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
