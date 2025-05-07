import logging
from datetime import datetime

from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from rest_framework import status

from api.operations import ContractOperations, CsrfOperations, PartyOperations
from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_info, log_error
logger = logging.getLogger(__name__)

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
        all_contracts, contracts = contract_ops.list_contracts(), []

        for contract in all_contracts:
            if "last_updated" in contract and contract["last_updated"]:
                contract["last_updated"] = datetime.fromisoformat(contract["last_updated"].rstrip("Z")).strftime("%Y-%m-%d %I:%M %p")

            parties = party_ops.get_parties(contract["contract_type"], contract["contract_idx"])
            for party in parties:
                if party["party_code"].lower() == customer.lower():
                    contracts.append(contract)

        # Handle sorting
        ordering = request.GET.get("ordering", "contract_idx")
        reverse = ordering.startswith("-")
        ordering_field = ordering.lstrip("-")

        if contracts and ordering_field in contracts[0]:
            contracts.sort(key=lambda x: x.get(ordering_field, ""), reverse=reverse)

        # Sorting links
        sorting_links = {
            "contract_idx": f"?ordering={'-' if ordering == 'contract_idx' else ''}contract_idx",
            "contract_name": f"?ordering={'-' if ordering == 'contract_name' else ''}contract_name",
            "is_quote": f"?ordering={'-' if ordering == 'is_quote' else ''}is_quote",
            "is_active": f"?ordering={'-' if ordering == 'is_active' else ''}is_active",
        }

        form_context = {
            "contracts": contracts,
            "ordering": ordering,
            "sorting_links": sorting_links,
            "customer": customer
        }

        log_info(logger, f"Form context: {form_context}")
        return render(request, "dashboard/list_contracts.html", form_context)

    except Exception as e:
        log_error(logger, f"Error in list_contracts_view: {e}")
        return render(request, "dashboard/list_contracts.html", {
            "error": "Error loading contracts"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)