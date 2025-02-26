import logging
from datetime import datetime
from decimal import Decimal

from django.shortcuts import render, redirect
from django.contrib import messages

from api.config import ConfigManager
from api.interfaces import ArtifactAPI
from api.secrets import SecretsManager
from api.registry import RegistryManager
from api.operations import ContractOperations, SettlementOperations, TransactionOperations
from api.operations import CsrfOperations, PartyOperations, ArtifactOperations
from api.utilities.logging import log_info, log_warning, log_error

from frontend.forms import PartyForm, ArtifactForm
from frontend.forms import AdvanceSettlementForm, SaleSettlementForm
from frontend.forms import AdvanceContractForm, SaleContractForm, PurchaseContractForm

logger = logging.getLogger(__name__)

# Helper function to initialize headers and configuration
def initialize_backend_services():
    secrets_manager = SecretsManager()
    registry_manager = RegistryManager()
    config_manager = ConfigManager()

    headers = {
        'Authorization': f"Api-Key {secrets_manager.get_master_key()}",
        'Content-Type': 'application/json',
    }

    csrf_ops = CsrfOperations(headers, config_manager.get_base_url())
    csrf_token = csrf_ops.get_csrf_token()

    return headers, registry_manager, config_manager, csrf_token

# Main view
def view_contract_view(request, extra_context=None):
    headers, registry_manager, config_manager, csrf_token = initialize_backend_services()
    contract_idx = request.GET.get("contract_idx")
    contract_type = request.GET.get("contract_type")

    log_info(logger, f"Fetching {contract_type}:{contract_idx}")

    if not contract_idx:
        messages.error(request, "Missing contract index.")
        return redirect("custom_admin:list_contracts")

    if not contract_type:
        messages.error(request, "Missing contract type.")
        return redirect("custom_admin:list_contracts")

    base_url = config_manager.get_base_url()

    if request.method == 'POST':
        return handle_post_request(request, registry_manager, contract_type, contract_idx, headers, base_url, csrf_token)

    # Prepare context and render the appropriate template
    context = prepare_view_context(request, registry_manager, contract_type, contract_idx, headers, base_url, csrf_token, extra_context)
    return render(request, f"admin/view_{contract_type}_contract.html", context)

# Handle POST requests for different forms
def handle_post_request(request, registry_manager, contract_type, contract_idx, headers, base_url, csrf_token):
    form_type = request.POST.get("form_type")

    log_info(logger, f"Handling form submission: {form_type}")

    form_handlers = {
        "contract": _update_contract,
        "parties": _update_parties,
        "settlements": _update_settlements,
        "artifacts": _update_artifacts,
    }

    handler = form_handlers.get(form_type)
    if handler:
        return handler(request, registry_manager, contract_type, contract_idx, headers, base_url, csrf_token)

    messages.error(request, "Invalid form type. Please correct the form and try again.")
    return redirect(f"/admin/view-contract/?contract_idx={contract_idx}?contract_type={contract_type}")

# Prepare context for rendering the view
def prepare_view_context(request, registry_manager, contract_type, contract_idx, headers, base_url, csrf_token, extra_context=None):
    contract_ops = ContractOperations(headers, base_url, csrf_token)

    try:
        contract = contract_ops.get_contract(contract_type, contract_idx)
        log_info(logger, f"Returned contract {contract}")
    except Exception as e:
        log_error(logger, f"Failed to fetch {contract_type}:{contract_idx}: {e}")
        messages.error(request, f"Failed to fetch {contract_type} contract {contract_idx}")
        return {}

    # Fetch related data
    try:
        log_info(logger, "Fetching settlements")
        settlements=[]
        if registry_manager.get_settlement_api(contract_type):
            settlements = fetch_settlements(contract_type, contract_idx, headers, base_url)
            log_info(logger, f"Retrieved settlements for {contract_type}:{contract_idx}: {settlements}")

        parties = fetch_parties(contract_type, contract_idx, headers, base_url)
        transactions = fetch_transactions(contract_type, contract_idx, headers, base_url)
        artifacts = fetch_artifacts(contract_type, contract_idx, headers, base_url)

    except Exception as e:
        log_error(logger, f"Failed to fetch related data for {contract_type}:{contract_idx}: {e}")
        messages.error(request, f"Failed to fetch related data.")

    # Generate presigned URLs for artifacts
    for artifact in artifacts:
        try:
            artifact['presigned_url'] = generate_presigned_url(artifact)
        except Exception as e:
            log_error(logger, f"Failed to generate presigned URL for artifact {artifact['doc_title']}: {e}")
            artifact['presigned_url'] = None
            messages.error(request, f"Failed to generate presigned URL for {artifact['doc_title']}.")

    # Choose the correct contract form based on type
    contract_form_template  = registry_manager.get_contract_form(contract_type)
    contract_form = contract_form_template(initial=contract)

    settlement_form = None
    if registry_manager.get_settlement_form(contract_type):
        settlement_form_template = registry_manager.get_settlement_form(contract_type)
        settlement_form = settlement_form_template(initial=contract)

    # Prepare context
    context = {
        'contract_idx': contract_idx,
        'contract_type': contract_type,
        'contract_form': contract_form,
        'party_form': PartyForm(),
        'settlement_form': settlement_form,
        'artifact_form': ArtifactForm(),
        'settlements': settlements,
        'parties': parties,
        'transactions': transactions,
        'artifacts': artifacts
    }

    if extra_context:
        context.update(extra_context)

    return context

# Generate presigned URL for artifacts
def generate_presigned_url(artifact):
    artifact_api = ArtifactAPI()
    return artifact_api.generate_presigned_url(
        s3_bucket=artifact['s3_bucket'],
        s3_object_key=artifact['s3_object_key'],
        s3_version_id=artifact.get('s3_version_id')
    )

# Update contract
def _update_contract(request, registry_manager, contract_type, contract_idx, headers, base_url, csrf_token):
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
def _update_parties(request, registry_manager, contract_type, contract_idx, headers, base_url, csrf_token):
    party_form = PartyForm(request.POST)

    if party_form.is_valid():
        payload = [party_form.cleaned_data]
        party_ops = PartyOperations(headers, base_url, csrf_token)

        try:
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
def _update_settlements(request, registry_manager, contract_type, contract_idx, headers, base_url, csrf_token):
    settlement_form_type = registry_manager.get_settlement_form(contract_type)
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
def _update_artifacts(request, registry_manager, contract_type, contract_idx, headers, base_url, csrf_token):
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