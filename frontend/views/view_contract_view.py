from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
from api.managers import ConfigManager, SecretsManager
from api.interfaces import ArtifactAPI
from frontend.forms import ContractForm, PartyForm, SettlementForm, ArtifactForm
from django.utils.safestring import mark_safe
from datetime import datetime

import json
import logging
import requests

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
    base_url = config["url"]

    form_handlers = {
        "contract": _update_contract,
        "parties": _update_parties,
        "settlements": _update_settlements,
        "artifacts": _update_artifacts,
        "artifact_urls": _add_artifact_urls
    }

    handler = form_handlers.get(form_type)
    if handler:
        return handler(request, contract_idx, headers, base_url)
    
    messages.error(request, "Invalid form type. Please correct the form and try again.")
    return redirect(request.path)

# Prepare context for rendering the view
def prepare_view_context(contract_idx, headers, config, extra_context=None):
    base_url = config["url"]

    # Fetch related data
    contract = _fetch_data(f"{base_url}/api/contracts/{contract_idx}/", headers)
    settlements = fetch_settlements(contract_idx, headers, config)
    parties = fetch_parties(contract_idx, headers, config)
    transactions = fetch_transactions(contract_idx, headers, config)
    artifacts = fetch_artifacts(contract_idx, headers, config)

    logger.info(f"artifacts: {artifacts}")

    # Generate presigned URLs for artifacts
    artifact_api = ArtifactAPI()  # Assuming you have access to ArtifactAPI
    for artifact in artifacts:
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
def _update_contract(request, contract_idx, headers, base_url):
    contract_form = ContractForm(request.POST)
    if contract_form.is_valid():
        payload = contract_form.cleaned_data
        url = f"{base_url}/api/contracts/{contract_idx}/"
        try:
            response = requests.patch(url, json=payload, headers=headers)
            response.raise_for_status()
            messages.success(request, "Contract updated successfully.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update contract: {e}")
            messages.error(request, "Failed to update contract.")
    else:
        messages.error(request, f"Invalid contract data: {contract_form.errors}")

    return redirect(f"/admin/view-contract/?contract_idx={contract_idx}")

# Update parties
def _update_parties(request, contract_idx, headers, base_url):
    party_form = PartyForm(request.POST)

    if party_form.is_valid():

        # payload must be a list
        payload = [party_form.cleaned_data]

        logger.info(f"payload: {payload}")

        url = f"{base_url}/api/contracts/{contract_idx}/parties/"
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            messages.success(request, "Party added successfully.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update parties: {e}")
            messages.error(request, "Failed to update parties.")
    else:
        messages.error(request, f"Invalid party data: {party_form.errors}")

    return redirect(f"/admin/view-contract/?contract_idx={contract_idx}")

# Update settlements
def _update_settlements(request, contract_idx, headers, base_url):
    settlement_form = SettlementForm(request.POST)

    if settlement_form.is_valid():
        payload = settlement_form.cleaned_data

        # Convert datetime fields to ISO 8601 format
        for field in ["settle_due_dt", "transact_min_dt", "transact_max_dt"]:
            if field in payload and isinstance(payload[field], datetime):
                payload[field] = payload[field].isoformat()

        # Construct the API URL
        url = f"{base_url}/api/contracts/{contract_idx}/settlements/"

        # Add default fields
        payload.update({
            "extended_data": {},
        })

        try:
            # Send the POST request to the API
            response = requests.post(url, json=[payload], headers=headers)
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
def _update_artifacts(request, contract_idx, headers, base_url):
    artifact_form = ArtifactForm(request.POST)

    if artifact_form.is_valid():
        payload = artifact_form.cleaned_data
        url = f"{base_url}/api/contracts/{contract_idx}/artifacts/"

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            messages.success(request, "Artifact added successfully.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update artifacts: {e}")
            messages.error(request, "Failed to update artifacts.")
    else:
        messages.error(request, f"Invalid artifact data: {artifact_form.errors}")

    return redirect(f"/admin/view-contract/?contract_idx={contract_idx}")

# Fetch related data
def fetch_parties(contract_idx, headers, config):
    return _fetch_related_data(contract_idx, "parties", headers, config)

def fetch_settlements(contract_idx, headers, config):
    return _fetch_related_data(contract_idx, "settlements", headers, config)

def fetch_transactions(contract_idx, headers, config):
    return _fetch_related_data(contract_idx, "transactions", headers, config)

def fetch_artifacts(contract_idx, headers, config):
    return _fetch_related_data(contract_idx, "artifacts", headers, config)

def _add_artifact_urls(request, contract_idx, headers, base_url):
    artifact_urls = request.POST.getlist("artifact_urls")

    if not artifact_urls:
        messages.error(request, "No artifact URLs provided.")
        return redirect(f"/admin/view-contract/?contract_idx={contract_idx}")

    url = f"{base_url}/api/contracts/{contract_idx}/artifacts/"

    payload = {"artifact_urls": artifact_urls}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        messages.success(request, "Artifacts uploaded successfully.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to upload artifacts: {e}")
        messages.error(request, "Failed to upload artifacts.")

    return redirect(f"/admin/view-contract/?contract_idx={contract_idx}")

def _fetch_related_data(contract_idx, endpoint, headers, config):
    base_url = config["url"]
    return _fetch_data(f"{base_url}/api/contracts/{contract_idx}/{endpoint}/", headers)

def _fetch_data(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from {url}: {e}")
        return {}

