import logging
import requests

from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
from rest_framework import status

from frontend.forms import ContractForm, PartyForm, SettlementForm, ArtifactForm

from api.managers import ConfigManager, SecretsManager
from api.operations import ContractOperations, SettlementOperations, TransactionOperations
from api.operations import CsrfOperations, PartyOperations, ArtifactOperations
from api.interfaces import ArtifactAPI

from api.utilities.logging import log_info, log_warning, log_error

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

    csrf_ops = CsrfOperations(headers, config)
    csrf_token = csrf_ops.get_csrf_token()

    return headers, config, csrf_token

# Main view
def view_contract_view(request, extra_context=None):
    headers, config, csrf_token = initialize_backend_services()
    contract_idx = request.GET.get("contract_idx")

    if request.method == 'POST':
        return handle_post_request(request, contract_idx, headers, config, csrf_token)

    # Initialize forms
    context = prepare_view_context(request, contract_idx, headers, config, extra_context)
    return render(request, "admin/view_contract.html", context)

# Handle POST requests for different forms
def handle_post_request(request, contract_idx, headers, config, csrf_token):
    form_type = request.POST.get("form_type")

    log_info(logger, f"form type: {form_type}")

    form_handlers = {
        "contract": _update_contract,
        "parties": _update_parties,
        "settlements": _update_settlements,
        "artifacts": _update_artifacts,
    }

    handler = form_handlers.get(form_type)
    if handler:
        return handler(request, contract_idx, headers, config, csrf_token)
    
    messages.error(request, "Invalid form type. Please correct the form and try again.")
    return redirect(request.path)

# Prepare context for rendering the view
def prepare_view_context(request, contract_idx, headers, config, extra_context=None):
    contract_ops = ContractOperations(headers, config)

    try:
        contract = contract_ops.get_contract(contract_idx)
    except Exception as e:
        error_message = f"Failed to fetch contract {contract_idx}"
        log_error(logger, f"{error_message}: {e}")
        messages.error(request, f"{error_message}")

    try:
        settlements = fetch_settlements(contract_idx, headers, config)
        parties = fetch_parties(contract_idx, headers, config)
        transactions = fetch_transactions(contract_idx, headers, config)
        artifacts = fetch_artifacts(contract_idx, headers, config)
    except Exception as e:
        error_message = f"Failed to fetch contract data for contract {contract_idx}"
        log_error(logger, f"{error_message}: {e}")
        messages.error(request, f"{error_message}")

    # Generate presigned URLs for artifacts
    artifact_api = ArtifactAPI()  

    for artifact in artifacts:
        log_info(logger, f"artifact: {artifact}")
        try:
            artifact['presigned_url'] = artifact_api.generate_presigned_url(
                s3_bucket=artifact['s3_bucket'],
                s3_object_key=artifact['s3_object_key'],
                s3_version_id=artifact.get('s3_version_id')
            )
        except Exception as e:
            error_message = f"Failed to generate presigned URL for artifact {artifact['doc_title']}"
            log_error(logger, f"{error_message}: {e}")
            artifact['presigned_url'] = None  # Fallback if URL generation fails
            messages.error(request, f"{error_message}")

    # Initialize forms
    contract_form = ContractForm(initial=contract)
    party_form = PartyForm()
    settlement_form = SettlementForm()
    artifact_form = ArtifactForm()

    # Hide specific fields
    fields_to_hide = [
        "funding_method", "funding_token_symbol", "funding_account", 
        "funding_recipient", "deposit_method", "deposit_token_symbol", 
        "deposit_account", "extended_data"
    ]
    for field_name in fields_to_hide:
        if field_name in contract_form.fields:
            contract_form.fields[field_name].widget = forms.HiddenInput()

    # reset these fields that are hidden in the add_contract form
    contract_form.fields['funding_instr'].widget = forms.Textarea(attrs={
        "readonly": "readonly", 
        "rows": 10, 
        "id": "funding-instr", 
        "style": "width: 100%;"
    })

    contract_form.fields['deposit_instr'].widget = forms.Textarea(attrs={
        "readonly": "readonly", 
        "rows": 10, 
        "id": "deposit-instr", 
        "style": "width: 100%;"
    })

    contract_form.fields['transact_logic'].widget = forms.Textarea(attrs={
        "readonly": "readonly", 
        "rows": 10, 
        "id": "transact-logic", 
        "style": "width: 100%;"
    })

    # Prepare context
    context = {
        'contract_idx': contract_idx,
        'contract_form': contract_form,
        'party_form': party_form,
        'settlement_form': settlement_form,
        'artifact_form': artifact_form,
        'settlements': settlements,
        'parties': parties,
        'transactions': transactions,
        'artifacts': artifacts
    }

    log_info(logger, f"extra_context: {extra_context}")

    if extra_context:
        context.update(extra_context)

    return context

# Update contract
def _update_contract(request, contract_idx, headers, config, csrf_token):
    contract_form = ContractForm(request.POST)

    if contract_form.is_valid():
        payload = contract_form.cleaned_data
        contract_ops = ContractOperations(headers, config, csrf_token)

        try:
            response = contract_ops.patch_contract(contract_idx, payload)
            if response["contract_idx"] == contract_idx:
                messages.success(request, "Contract updated successfully.")
            else:
                raise RuntimeError

        except Exception as e:
            error_message = f"Failed to update contract"
            log_error(logger, f"{error_message}: {e}")
            messages.error(request, f"{error_message}")
    else:
        messages.error(request, f"Invalid contract data: {contract_form.errors}")

    return redirect(f"/admin/view-contract/?contract_idx={contract_idx}")

# Update parties
def _update_parties(request, contract_idx, headers, config, csrf_token):
    party_form = PartyForm(request.POST)

    if party_form.is_valid():
        payload = [party_form.cleaned_data]
        party_ops = PartyOperations(headers, config, csrf_token)

        try:
            response = party_ops.post_parties(contract_idx, payload)
            if response["count"] > 0:
                messages.success(request, "Party added successfully.")
            else:
                raise RuntimeError

        except Exception as e:
            error_message = f"Failed to add parties"
            log_error(logger, f"{error_message}: {e}")
            messages.error(request, f"{error_message}")
    else:
        messages.error(request, f"Invalid party data: {party_form.errors}")

    return redirect(f"/admin/view-contract/?contract_idx={contract_idx}")

# Update settlements
def _update_settlements(request, contract_idx, headers, config, csrf_token):
    settlement_form = SettlementForm(request.POST)

    if settlement_form.is_valid():
        payload = settlement_form.cleaned_data
        settlement_ops = SettlementOperations(headers, config, csrf_token)

        # Convert datetime fields to ISO 8601 format
        for field in ["settle_due_dt", "transact_min_dt", "transact_max_dt"]:
            if field in payload and isinstance(payload[field], datetime):
                payload[field] = payload[field].isoformat()

        # Add default fields
        payload.update({"extended_data": {}})

        try:
            # Send the POST request to the API
            response = settlement_ops.post_settlements(contract_idx, [payload])
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
    return redirect(f"/admin/view-contract/?contract_idx={contract_idx}")

# Update artifacts
def _update_artifacts(request, contract_idx, headers, config, csrf_token):
    artifact_urls = request.POST.getlist("artifact_urls")

    if not artifact_urls:
        messages.error(request, "No artifact URLs provided.")
        return redirect(f"/admin/view-contract/?contract_idx={contract_idx}")

    artifact_ops = ArtifactOperations(headers, config, csrf_token)

    try:
        response = artifact_ops.post_artifacts(contract_idx, artifact_urls)
        if response["count"] > 0:
            messages.success(request, "Artifacts uploaded successfully.")
        else: 
            raise RuntimeError

    except Exception as e:
        error_message = f"Failed to add artifacts"
        log_error(logger, f"{error_message}: {e}")
        messages.error(request, f"{error_message}")

    return redirect(f"/admin/view-contract/?contract_idx={contract_idx}")

# Fetch related data
def fetch_parties(contract_idx, headers, config):
    party_ops = PartyOperations(headers, config)
    return party_ops.get_parties(contract_idx)

def fetch_settlements(contract_idx, headers, config):
    settlement_ops = SettlementOperations(headers, config)
    return settlement_ops.get_settlements(contract_idx)

def fetch_transactions(contract_idx, headers, config):
    transaction_ops = TransactionOperations(headers, config)
    return transaction_ops.get_transactions(contract_idx)

def fetch_artifacts(contract_idx, headers, config):
    artifact_ops = ArtifactOperations(headers, config)
    return artifact_ops.get_artifacts(contract_idx)

