import logging
import os
from datetime import datetime
from decimal import Decimal
from weasyprint import HTML, CSS
from pathlib import Path
from dateutil.parser import isoparse

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
from django.template.loader import render_to_string

from api.operations import ContractOperations, SettlementOperations, TransactionOperations
from api.operations import CsrfOperations, PartyOperations, ArtifactOperations
from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_info, log_warning, log_error

from frontend.forms import PartyForm, ArtifactForm, AdvanceContractForm

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
def view_contract_view(request, extra_context=None):
    headers, context, csrf_token = initialize_backend_services()
    contract_idx = request.GET.get("contract_idx")
    contract_type = request.GET.get("contract_type")

    log_info(logger, f"Fetching {contract_type}:{contract_idx}")

    if not contract_idx:
        messages.error(request, "Missing contract index.")
        return redirect("custom_admin:list_contracts")

    if not contract_type:
        messages.error(request, "Missing contract type.")
        return redirect("custom_admin:list_contracts")

    base_url = context.config_manager.get_base_url()

    if request.method == 'POST':
        return handle_post_request(request, context, contract_type, contract_idx, headers, base_url, csrf_token)

    # Prepare form_context and render the appropriate template
    form_context = prepare_view_form_context(request, context, contract_type, contract_idx, headers, base_url, csrf_token, extra_context)
    return render(request, f"admin/view_{contract_type}_contract.html", form_context)

# Handle POST requests for different forms
def handle_post_request(request, context, contract_type, contract_idx, headers, base_url, csrf_token):
    form_type = request.POST.get("form_type")

    log_info(logger, f"Handling form submission: {form_type}")

    form_handlers = {
        "contract": _update_contract,
        "parties": _update_parties,
        "settlements": _update_settlements,
        "artifacts": _update_artifacts,
        "generate_report": _generate_report
    }

    handler = form_handlers.get(form_type)
    log_info(logger, f"Calling {form_type} with contract {contract_idx} and contract_type {contract_type}")

    if handler:
        return handler(request, context, contract_type, contract_idx, headers, base_url, csrf_token)

    messages.error(request, "Invalid form type. Please correct the form and try again.")
    return redirect(f"/admin/view-contract/?contract_idx={contract_idx}?contract_type={contract_type}")

# Prepare form_context for rendering the view
def prepare_view_form_context(request, context, contract_type, contract_idx, headers, base_url, csrf_token, extra_context=None):
    contract_ops = ContractOperations(headers, base_url, csrf_token)

    try:
        contract = contract_ops.get_contract(contract_type, contract_idx)
        log_info(logger, f"Returned contract {contract}")
    except Exception as e:
        log_error(logger, f"Failed to fetch {contract_type}:{contract_idx}: {e}")
        messages.error(request, f"Failed to fetch {contract_type} contract {contract_idx}")
        return {}

    # Extract fields from funding_instr
    funding_instr = contract.get("funding_instr", {})
    if funding_instr.get("bank") == "token":
        symbol = funding_instr.get("token_symbol")
        network = funding_instr.get("network")
        if symbol and network:
            contract["funding_token_symbol"] = f"{network}:{symbol}"
            contract["funding_token_network"] = network

    # Extract fields from deposit_instr
    deposit_instr = contract.get("deposit_instr", {})
    if deposit_instr.get("bank") == "token":
        symbol = deposit_instr.get("token_symbol")
        network = deposit_instr.get("network")
        if symbol and network:
            contract["deposit_token_symbol"] = f"{network}:{symbol}"
            contract["deposit_token_network"] = network

    # Fetch related data
    try:
        log_info(logger, "Fetching settlements")
        settlements=[]
        if context.api_manager.get_settlement_api(contract_type):
            settlements = fetch_settlements(contract_type, contract_idx, headers, base_url)
            log_info(logger, f"Retrieved settlements for {contract_type}:{contract_idx}: {settlements}")

        parties = fetch_parties(contract_type, contract_idx, headers, base_url)
        transactions = fetch_transactions(contract_type, contract_idx, headers, base_url)
        artifacts = fetch_artifacts(contract_type, contract_idx, headers, base_url)
        log_info(logger, f"artifacts: {artifacts}")

    except Exception as e:
        log_error(logger, f"Failed to fetch related data for {contract_type}:{contract_idx}: {e}")
        messages.error(request, f"Failed to fetch related data.")

    # Generate presigned URLs for artifacts
    for artifact in artifacts:
        try:
            artifact['presigned_url'] = generate_presigned_url(artifact, context.api_manager)
        except Exception as e:
            log_error(logger, f"Failed to generate presigned URL for artifact {artifact['doc_title']}: {e}")
            artifact['presigned_url'] = None
            messages.error(request, f"Failed to generate presigned URL for {artifact['doc_title']}.")

    # Choose the correct contract form based on type
    banks = context.domain_manager.get_banks()

    token_list = []
    token_config = context.config_manager.get_all_token_addresses()
    for entry in token_config:
        network = entry["key"]
        for token in entry.get("value", []):
            symbol = token["key"]
            token_list.append(f"{network}:{symbol}")

    contract_form_template  = context.form_manager.get_contract_form(contract_type)
    contract_form = contract_form_template(initial=contract, banks=banks, token_list=token_list)

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
        'artifacts': artifacts
    }

    if extra_context:
        form_context.update(extra_context)

    return form_context

# Generate presigned URL for artifacts
def generate_presigned_url(artifact, api_manager):

    artifact_api = api_manager.get_artifact_api()

    return artifact_api.generate_presigned_url(
        s3_bucket=artifact['s3_bucket'],
        s3_object_key=artifact['s3_object_key'],
        s3_version_id=artifact.get('s3_version_id')
    )

# Update contract
def _update_contract(request, context, contract_type, contract_idx, headers, base_url, csrf_token):
    contract_form = AdvanceContractForm(request.POST, view_mode=True)

    if contract_form.is_valid():
        payload = contract_form.cleaned_data
        contract_ops = ContractOperations(headers, base_url, csrf_token)

        try:
            response = contract_ops.patch_contract(contract_idx, payload)
            if response["contract_idx"] == contract_idx:
                messages.success(request, "Contract updated successfully.")
            else:
                raise RuntimeError

        except Exception as e:
            log_error(logger, f"Failed to update contract: {e}")
            messages.error(request, "Failed to update contract.")
    else:
        messages.error(request, f"Invalid contract data: {contract_form.errors}")

    return redirect(f"/admin/view-contract/?contract_idx={contract_idx}&contract_type={contract_type}")

# Update parties
def _update_parties(request, context, contract_type, contract_idx, headers, base_url, csrf_token):

    party_codes = context.config_manager.get_party_codes()
    party_types = context.domain_manager.get_party_types()
    party_form = PartyForm(request.POST, party_codes=party_codes, party_types=party_types)

    if party_form.is_valid():
        payload = [party_form.cleaned_data]
        party_ops = PartyOperations(headers, base_url, csrf_token)

        try:
            log_info(logger, f"Posting: {contract_type}, {contract_idx}, {payload}")
            response = party_ops.post_parties(contract_type, contract_idx, payload)
            if response["count"] > 0:
                messages.success(request, "Party added successfully.")
            else:
                raise RuntimeError

        except Exception as e:
            log_error(logger, f"Failed to add parties: {e}")
            messages.error(request, "Failed to add parties.")
    else:
        messages.error(request, f"Invalid party data: {party_form.errors}")

    return redirect(f"/admin/view-contract/?contract_idx={contract_idx}&contract_type={contract_type}")

# Update settlements
def _update_settlements(request, context, contract_type, contract_idx, headers, base_url, csrf_token):
    settlement_form_type = context.form_manager.get_settlement_form(contract_type)
    settlement_form = settlement_form_type(request.POST)

    if settlement_form.is_valid():
        payload = settlement_form.cleaned_data
        settlement_ops = SettlementOperations(headers, base_url, csrf_token)

        # Convert datetime fields to ISO 8601 format
        for field in ["settle_due_dt", "transact_min_dt", "transact_max_dt"]:
            if field in payload and isinstance(payload[field], datetime):
                payload[field] = payload[field].isoformat()

        # Convert Decimal fields to float
        for field in ["principal_amt", "settle_exp_amt"]:
            if field in payload and isinstance(payload[field], Decimal):
                payload[field] = float(payload[field])

        # Add default fields
        payload.update({"extended_data": {}})
        log_info(logger, f"Settlement payload: {payload}")

        try:
            # Send the POST request to the API
            response = settlement_ops.post_settlements(contract_type, contract_idx, [payload])
            if response["count"] > 0:
                messages.success(request, "Settlement added successfully.")
            else:
                raise RuntimeError

        except Exception as e:
            error_message = f"Failed to add settlements"
            log_error(logger, f"{error_message}: {e}")
            messages.error(request, f"{error_message}")
    else:
        # Form validation failed; show the errors
        messages.error(request, f"Invalid settlement data: {settlement_form.errors}")

    # Redirect back to the contract view
    return redirect(f"/admin/view-contract/?contract_idx={contract_idx}&contract_type={contract_type}")

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

        contract = contract_ops.get_contract(contract_type, contract_idx)
        parties = party_ops.get_parties(contract_type, contract_idx)
        transactions = transact_ops.get_transactions(contract_type, contract_idx)
        artifacts = artifact_ops.get_artifacts(contract_type, contract_idx)

        settlements = {}
        if context.api_manager.get_settlement_api(contract_type):
            settlements = context.api_manager.get_settlement_api(contract_type).get_settlements(contract_type, contract_idx)

        # Resolve file:// path to the logo for WeasyPrint
        logo_file_path = os.path.join(settings.BASE_DIR, 'frontend/static/assets/logo/fizit_full_color.png')
        logo_url = f'file://{logo_file_path}'

        # Calculate display-friendly fields
        if contract.get("service_fee_pct") is not None:
            contract["service_fee_pct"] = round(float(contract["service_fee_pct"]) * 100, 4)

        for transaction in transactions:
            transaction["transact_dt"] = isoparse(transaction["transact_dt"])

        for artifact in artifacts:
            artifact["added_dt"] = isoparse(artifact["added_dt"])

        # Render HTML using a simple template (you can improve this later)
        html_string = render_to_string("reports/contract_report.html", {
            "contract": contract,
            "parties": parties,
            "transactions": transactions,
            "artifacts": artifacts,
            "settlements": settlements,
            "contract_idx": contract_idx,
            "contract_type": contract_type,
            "report_date": datetime.utcnow(),
            "logo_url": logo_url
        })

        # Generate PDF from HTML
        pdf = HTML(
            string=html_string,
            base_url=str(Path(settings.BASE_DIR) / "frontend/templates/reports/")
        ).write_pdf()

        # Return response as download
        contract_name = contract.get("contract_name")
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{contract_name}.pdf"'
        return response

    except Exception as e:
        log_error(logger, f"Failed to generate report for {contract_type}:{contract_idx}: {e}")
        messages.error(request, "Failed to generate report.")
        return redirect(f"/admin/view-contract/?contract_idx={contract_idx}&contract_type={contract_type}")