import json
import logging
import requests

from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms

from frontend.forms import ContractForm, PartyForm, SettlementForm, ArtifactForm

from api.managers import ConfigManager, SecretsManager
from api.operations import ContractOperations, SettlementOperations, TransactionOperations
from api.operations import CsrfOperations, PartyOperations, ArtifactOperations
from api.interfaces import ArtifactAPI

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

# Main view
def view_contract_view(request, extra_context=None):
    headers, config = initialize_backend_services()
    contract_idx = request.GET.get("contract_idx")

    if request.method == 'POST':
        return handle_post_request(request, contract_idx, headers, config)

    # Initialize forms
    context = prepare_view_context(contract_idx, headers, config, extra_context)
    return render(request, "admin/view_contract.html", context)

# Handle POST requests for different forms
def handle_post_request(request, contract_idx, headers, config):
    form_type = request.POST.get("form_type")

    logger.info(f"form type: {form_type}")

    form_handlers = {
        "contract": _update_contract,
        "parties": _update_parties,
        "settlements": _update_settlements,
        "artifacts": _update_artifacts,
    }

    handler = form_handlers.get(form_type)
    if handler:
        return handler(request, contract_idx, headers, config)
    
    messages.error(request, "Invalid form type. Please correct the form and try again.")
    return redirect(request.path)

# Prepare context for rendering the view
def prepare_view_context(contract_idx, headers, config, extra_context=None):

    contract_ops = ContractOperations(headers, config)
    contract = contract_ops.get_contract(contract_idx).json()

    settlements = fetch_settlements(contract_idx, headers, config)
    parties = fetch_parties(contract_idx, headers, config)
    transactions = fetch_transactions(contract_idx, headers, config)
    artifacts = fetch_artifacts(contract_idx, headers, config)

    # Generate presigned URLs for artifacts
    artifact_api = ArtifactAPI()  

    for artifact in artifacts:
        logger.info(f"artifact: {artifact}")
        try:
            artifact['presigned_url'] = artifact_api.generate_presigned_url(
                s3_bucket=artifact['s3_bucket'],
                s3_object_key=artifact['s3_object_key'],
                s3_version_id=artifact.get('s3_version_id')
            )
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for artifact {artifact['doc_title']}: {e}")
            artifact['presigned_url'] = None  # Fallback if URL generation fails

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
    if extra_context:
        context.update(extra_context)

    return context

# Update contract
def _update_contract(request, contract_idx, headers, config):
    contract_form = ContractForm(request.POST)
    if contract_form.is_valid():
        payload = contract_form.cleaned_data
        contract_ops = ContractOperations(headers, config)

        try:
            response = contract_ops.patch_contract(contract_idx, payload)
            response.raise_for_status()
            messages.success(request, "Contract updated successfully.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update contract: {e}")
            messages.error(request, "Failed to update contract.")
    else:
        messages.error(request, f"Invalid contract data: {contract_form.errors}")

    return redirect(f"/admin/view-contract/?contract_idx={contract_idx}")

# Update parties
def _update_parties(request, contract_idx, headers, config):
    party_form = PartyForm(request.POST)

    if party_form.is_valid():
        payload = [party_form.cleaned_data]
        party_ops = PartyOperations(headers, config)

        try:
            response = party_ops.add_parties(contract_idx, payload)
            response.raise_for_status()
            messages.success(request, "Party added successfully.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update parties: {e}")
            messages.error(request, "Failed to update parties.")
    else:
        messages.error(request, f"Invalid party data: {party_form.errors}")

    return redirect(f"/admin/view-contract/?contract_idx={contract_idx}")

# Update settlements
def _update_settlements(request, contract_idx, headers, config):
    settlement_form = SettlementForm(request.POST)

    if settlement_form.is_valid():
        payload = settlement_form.cleaned_data
        settlement_ops = SettlementOperations(headers, config)

        # Convert datetime fields to ISO 8601 format
        for field in ["settle_due_dt", "transact_min_dt", "transact_max_dt"]:
            if field in payload and isinstance(payload[field], datetime):
                payload[field] = payload[field].isoformat()

        # Add default fields
        payload.update({
            "extended_data": {},
        })

        try:
            # Send the POST request to the API
            response = settlement_ops.post_settlements(contract_idx, [payload])
            response.raise_for_status()
            
            # Success message
            messages.success(request, "Settlement added successfully.")
        except requests.exceptions.RequestException as e:
            # Log the error and display an error message
            logger.error(f"Failed to update settlements: {e}")
            messages.error(request, "Failed to update settlements.")
    else:
        # Form validation failed; show the errors
        messages.error(request, f"Invalid settlement data: {settlement_form.errors}")

    # Redirect back to the contract view
    return redirect(f"/admin/view-contract/?contract_idx={contract_idx}")

# Update artifacts
def _update_artifacts(request, contract_idx, headers, config):

    csrf_ops = CsrfOperations(headers, config)
    artifact_urls = request.POST.getlist("artifact_urls")

    if not artifact_urls:
        messages.error(request, "No artifact URLs provided.")
        return redirect(f"/admin/view-contract/?contract_idx={contract_idx}")

    artifact_ops = ArtifactOperations(headers, config)

    try:
        csrf_token = csrf_ops.get_csrf_token()
        response = artifact_ops.add_artifacts(contract_idx, artifact_urls, csrf_token)
        response.raise_for_status()
        messages.success(request, "Artifacts uploaded successfully.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to upload artifacts: {e}")
        messages.error(request, "Failed to upload artifacts.")

    return redirect(f"/admin/view-contract/?contract_idx={contract_idx}")

# Fetch related data
def fetch_parties(contract_idx, headers, config):
    party_ops = PartyOperations(headers, config)
    return party_ops.get_parties(contract_idx).json()

def fetch_settlements(contract_idx, headers, config):
    settlement_ops = SettlementOperations(headers, config)
    return settlement_ops.get_settlements(contract_idx).json()

def fetch_transactions(contract_idx, headers, config):
    transaction_ops = TransactionOperations(headers, config)
    return transaction_ops.get_transactions(contract_idx).json()

def fetch_artifacts(contract_idx, headers, config):
    artifact_ops = ArtifactOperations(headers, config)
    return artifact_ops.get_artifacts(contract_idx).json()

