import requests
import logging
import json

from datetime import datetime

from django.contrib import messages
from django.shortcuts import render, redirect

from api.operations import CsrfOperations, BankOperations, ContractOperations
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

def fetch_all_distributions(headers, context, base_url, csrf_token):
    bank_ops = BankOperations(headers, base_url, csrf_token)
    contract_ops = ContractOperations(headers, base_url, csrf_token)

    contract_types = context.domain_manager.get_contract_types()
    distributions=[]

    for contract_type in contract_types:
        if context.api_manager.get_distribution_api(contract_type):
            log_info(logger, f"Retrieving distributions for contract_type {contract_type}")

            try:
                count_response = contract_ops.get_count(contract_type)
            except requests.RequestException as e:
                log_error(logger, f"Failed to fetch contract count: {e}")
                return []

            contract_count = count_response['count']

            # Fetch distributions one by one
            for contract_idx in range(0, contract_count):
                try:
                    distribution = bank_ops.get_distributions(contract_type, contract_idx)
                    log_info(logger, f"Distribution for {contract_type}:{contract_idx}: {distribution}")
                    distributions.extend(distribution)
                except requests.RequestException as e:
                    log_error(logger, f"Failed to fetch distributions for contract {contract_type}:{contract_idx}: {e}")

    return distributions

def handle_post_request(request, headers, base_url, csrf_token):
    bank_ops = BankOperations(headers, base_url, csrf_token)

    try:
        # Retrieve selected distributions from the form
        distributions_json = request.POST.get("distributions")
        distributions_to_post = json.loads(distributions_json)
        log_info(logger, f"Post response: distributions: {distributions_to_post}")

        if not distributions_to_post:
            messages.error(request, "No valid distributions found for posting.")
            return redirect(request.path)

        for distribution in distributions_to_post:
            response = bank_ops.post_distributions(distribution["contract_type"], distribution["contract_idx"], [distribution])
            log_info(logger, f"Response from post: {response}")

            if "error" in response:
                log_error(logger, f"Failed to post distributions: {response}")
                messages.error(request, f"Failed to post distributions")
                return redirect(request.path)

        messages.success(request, "Distributions posted successfully.")

    except Exception as e:
        logger.exception(f"Unexpected error while posting distributions: {e}")
        messages.error(request, f"An unexpected error occurred: {str(e)}")

    return redirect(request.path)

# Main view
def add_distribution_view(request, extra_context=None):
    headers, context, csrf_token = initialize_backend_services()
    base_url = context.config_manager.get_base_url()

    # Extract contract_type from the GET parameters
    contract_type = request.GET.get("contract_type")
    log_info(logger, f"Selected contract_type: {contract_type}")

    if request.method == 'POST':
        # Delegate to the POST handler
        return handle_post_request(request, headers, base_url, csrf_token)

    # Fetch all contracts with prepopulated transact_data
    distributions = fetch_all_distributions(headers, context, base_url, csrf_token)
    log_info(logger, f"Retrieved distributions {distributions}")

    form_context = {
        "distributions": distributions 
    }

    if extra_context:
        form_context.update(extra_context)

    return render(request, "admin/add_distribution.html", form_context)