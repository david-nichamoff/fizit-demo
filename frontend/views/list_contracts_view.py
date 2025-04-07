import logging
import requests
from datetime import datetime

from rest_framework import status
from django.shortcuts import render
from django.contrib import messages

from api.operations import ContractOperations, CsrfOperations
from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_info, log_warning, log_error

logger = logging.getLogger(__name__)

def list_contracts_view(request, extra_context=None):
    context = build_app_context()

    try:
        # Initialize Config, Secrets, and Registry Managers

        headers = {
            "Authorization": f"Api-Key {context.secrets_manager.get_master_key()}",
            "Content-Type": "application/json",
        }

        csrf_ops = CsrfOperations(headers, context.config_manager.get_base_url())
        csrf_token = csrf_ops.get_csrf_token()
        contract_ops = ContractOperations(headers, context.config_manager.get_base_url(), csrf_token)

        # Get available contract types for filtering
        contract_types = context.domain_manager.get_contract_types()
        default_contract_type = context.domain_manager.get_default_contract_type()
        selected_contract_type = request.GET.get("contract_type", default_contract_type)  

        try:
            # Fetch all contracts at once
            contracts = contract_ops.list_contracts()
            for contract in contracts:
                if "last_updated" in contract:
                    contract["last_updated"] = datetime.fromisoformat(contract["last_updated"].rstrip("Z")).strftime("%Y-%m-%d %I:%M %p")

            # Apply filtering by contract type
            contracts = [c for c in contracts if c.get("contract_type") == selected_contract_type]
        except Exception as e:
            error_message = f"Failed to fetch contract list"
            log_error(logger, f"{error_message}: {e}")
            messages.error(request, f"{error_message}")
            contracts = []

        # Handle sorting
        ordering = request.GET.get("ordering", "contract_idx") 
        reverse = ordering.startswith("-")
        ordering_field = ordering.lstrip("-")

        # Sort contracts if the field exists in the contract data
        if contracts and ordering_field in contracts[0]:
            contracts = sorted(contracts, key=lambda x: x.get(ordering_field, ""), reverse=reverse)

        # Prepare sorting links for the template
        sorting_links = {
            "contract_idx": f"?ordering={'-' if ordering == 'contract_idx' else ''}contract_idx&contract_type={selected_contract_type}",
            "contract_name": f"?ordering={'-' if ordering == 'contract_name' else ''}contract_name&contract_type={selected_contract_type}",
            "is_quote": f"?ordering={'-' if ordering == 'is_quote' else ''}is_quote&contract_type={selected_contract_type}",
            "is_active": f"?ordering={'-' if ordering == 'is_active' else ''}is_active&contract_type={selected_contract_type}",
        }

        # Prepare form_context
        form_context = {
            "contracts": contracts,
            "contract_types": contract_types,
            "selected_contract_type": selected_contract_type,
            "ordering": ordering,
            "sorting_links": sorting_links,
        }

        # Merge with extra_context if provided
        if extra_context:
            form_context.update(extra_context)

        return render(request, "admin/list_contracts.html", form_context)

    except Exception as e:
        error_message = "Error in list_contracts_view"
        log_error(logger, f"{error_message}: {e}")
        return render(request, "admin/list_contracts.html", {"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)