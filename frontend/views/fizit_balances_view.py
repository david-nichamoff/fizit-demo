import logging
from django.shortcuts import render, redirect
from eth_utils import to_checksum_address
from django.contrib import messages

from api.adapters.bank import TokenAdapter
from api.operations import CsrfOperations
from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_info, log_warning, log_error
from frontend.forms import TransferFundsForm

logger = logging.getLogger(__name__)

def initialize_backend_services():
    context = build_app_context()

    headers = {
        'Authorization': f"Api-Key {context.secrets_manager.get_master_key()}",
        'Content-Type': 'application/json',
    }

    csrf_token = CsrfOperations(headers, context.config_manager.get_base_url()).get_csrf_token()
    return headers, context, csrf_token

def get_fizit_balances(addresses, label, w3, context, logger):
    results = []
    if not addresses:
        log_warning(logger, f"No addresses found for {label}s.")
        return results

    for item in addresses:
        item_label = item.get("key", "Unknown")
        item_addr = item.get("value")

        if not item_addr or item_addr.lower() == context.web3_manager.get_zero_address():
            log_warning(logger, f"Skipping invalid or zero address for {item_label}.")
            continue

        try:
            checksum_addr = to_checksum_address(item_addr)
            balance_wei = w3.eth.get_balance(checksum_addr)
            readable_balance = w3.from_wei(balance_wei, 'ether')
            results.append({
                "label": item_label,
                "address": checksum_addr,
                "balance": readable_balance
            })
        except Exception as e:
            log_error(logger, f"Error checking FIZIT balance for {item_label}: {e}")
            results.append({"label": item_label, "address": item_addr, "balance": "Error"})
    return results

def handle_post_request(request, context, headers, csrf_token):
    from_address = request.POST.get("from_address")
    to_address = request.POST.get("to_address")
    amount = request.POST.get("amount")
    log_info(logger, f"Send {amount} from {to_address} to {from_address}")

    token_adapter = TokenAdapter(context)

    tx_hash = token_adapter.make_payment(
        contract_type=None,
        contract_idx=None,
        funder_addr=from_address,
        recipient_addr=to_address,
        network="fizit",
        token_symbol="FIZIT",  
        amount=amount
    )

    if tx_hash == 'MfaRequired':
        messages.success(request, f"Transaction signed successfully, approval required.")
    else:
        messages.success(request, f"Transaction posted successfully with tx_hash {tx_hash}.")

    return redirect(request.path)

def fizit_balances_view(request, extra_context=None):
    headers, context, csrf_token = initialize_backend_services()
    base_url = context.config_manager.get_base_url()
    w3 = context.web3_manager.get_web3_instance(network="fizit")

    if request.method == 'POST':
        return handle_post_request(request, context, headers, csrf_token)

    balances = {
        "wallets": get_fizit_balances(context.config_manager.get_wallet_addresses(), "Wallet", w3, context, logger),
        "parties": get_fizit_balances(context.config_manager.get_party_addresses(), "Party", w3, context, logger),
    }

    transfer_funds_form = TransferFundsForm()

    form_context = {
        "balances": balances,
        "transfer_funds_form": transfer_funds_form
    }

    if extra_context:
        form_context.update(extra_context)

    return render(request, "admin/fizit_balances.html", form_context)