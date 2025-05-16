import logging
from datetime import datetime

from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from rest_framework import status

from api.operations import ContractOperations, CsrfOperations, PartyOperations
from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_info, log_error

from frontend.views.decorators.group import group_matches_customer

logger = logging.getLogger(__name__)

@group_matches_customer
def list_contracts_view(request, customer):
    context = build_app_context()
    log_info(logger, f"Launching dashboard for {customer}")

    try:
        # Prepare headers with API Key (using master key for demo)
        headers = {
            "Authorization": f"Api-Key {context.secrets_manager.get_master_key()}",
            "Content-Type": "application/json",
        }

        csrf_ops = CsrfOperations(headers, context.config_manager.get_base_url())
        csrf_token = csrf_ops.get_csrf_token()
        contract_ops = ContractOperations(headers, context.config_manager.get_base_url(), csrf_token)
        party_ops = PartyOperations(headers, context.config_manager.get_base_url(), csrf_token)

        # Fetch contracts
        contracts = contract_ops.list_contracts_by_party_code(customer)

        # Sort by contract_type, then contract_idx (default)
        contracts.sort(key=lambda x: (x.get("contract_type", ""), int(x.get("contract_idx", 0))))
        
        # Title
        if customer == 'associated':
            list_title = "Associated Pipe Line Contracts"
        else:
            list_title = "FIZIT Contracts"

        form_context = {
            "contracts": contracts,
            "customer": customer,
            "list_title": list_title
        }

        log_info(logger, f"Form context: {form_context}")
        return render(request, "dashboard/list_contracts.html", form_context)

    except Exception as e:
        log_error(logger, f"Error in list_contracts_view: {e}")
        return render(request, "dashboard/list_contracts.html", {
            "error": "Error loading contracts"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)