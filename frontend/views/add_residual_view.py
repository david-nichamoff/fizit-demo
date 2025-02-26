import requests
import logging
import json

from datetime import datetime

from django.contrib import messages
from django.shortcuts import render, redirect

from api.config import ConfigManager
from api.secrets import SecretsManager
from api.registry import RegistryManager
from api.operations import CsrfOperations, BankOperations, ContractOperations
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

def fetch_all_residuals(headers, base_url, registry_manager, csrf_token):
    bank_ops = BankOperations(headers, base_url, csrf_token)
    contract_ops = ContractOperations(headers, base_url, csrf_token)

    contract_types = registry_manager.get_contract_types()
    residuals=[]

    for contract_type in contract_types:
        if registry_manager.get_residual_api(contract_type):
            log_info(logger, f"Retrieving residuals for contract_type {contract_type}")

            try:
                count_response = contract_ops.get_count(contract_type)
            except requests.RequestException as e:
                log_error(logger, f"Failed to fetch contract count: {e}")
                return []

            contract_count = count_response['count']

            # Fetch residuals one by one
            for contract_idx in range(0, contract_count):
                try:
                    residual = bank_ops.get_residuals(contract_type, contract_idx)
                    log_info(logger, f"Residual for {contract_type}:{contract_idx}: {residual}")
                    residuals.extend(residual)
                except requests.RequestException as e:
                    log_warning(logger, f"Failed to fetch residuals for contract {contract_type}:{contract_idx}: {e}")

    return residuals 

def handle_post_request(request, headers, base_url, csrf_token):
    bank_ops = BankOperations(headers, base_url, csrf_token)

    try:
        # Retrieve selected residuals from the form
        residuals_json = request.POST.get("residuals")
        residuals_to_post = json.loads(residuals_json)
        log_info(logger, f"Post response: residuals: {residuals_to_post}")

        if not residuals_to_post:
            messages.error(request, "No valid residuals found for posting.")
            return redirect(request.path)

        for residual in residuals_to_post:
            response = bank_ops.post_residuals(residual["contract_type"], residual["contract_idx"], [residual])
            log_info(logger, f"Response from post: {response}")

            if "error" in response:
                log_error(logger, f"Failed to post residuals: {response}")
                messages.error(request, f"Failed to post residuals")
                return redirect(request.path)

        messages.success(request, "Residuals posted successfully.")

    except Exception as e:
        logger.exception(f"Unexpected error while posting residuals: {e}")
        messages.error(request, f"An unexpected error occurred: {str(e)}")

    return redirect(request.path)

# Main view
def add_residual_view(request, extra_context=None):
    headers, registry_manager, config_manager, csrf_token = initialize_backend_services()
    base_url = config_manager.get_base_url()

    # Extract contract_type from the GET parameters
    contract_type = request.GET.get("contract_type")
    log_info(logger, f"Selected contract_type: {contract_type}")

    if request.method == 'POST':
        # Delegate to the POST handler
        return handle_post_request(request, headers, base_url, csrf_token)

    # Fetch all contracts with prepopulated transact_data
    residuals = fetch_all_residuals(headers, base_url, registry_manager, csrf_token)
    log_info(logger, f"Retrieved residuals {residuals}")

    context = {
        "residuals": residuals 
    }

    if extra_context:
        context.update(extra_context)

    return render(request, "admin/add_residual.html", context)