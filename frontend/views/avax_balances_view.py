import logging

from django.shortcuts import render, redirect
from django.contrib import messages

from eth_utils import to_checksum_address

from api.operations import CsrfOperations
from api.adapters.bank import TokenAdapter
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

    csrf_ops = CsrfOperations(headers, context.config_manager.get_base_url())
    csrf_token = csrf_ops.get_csrf_token()

    return headers, context, csrf_token

def get_avax_balances(addresses, label, w3, context, logger):
    """Helper to retrieve AVAX native token balances for wallets or parties."""
    results = []

    if not addresses:
        log_warning(logger, f"No addresses found for {label}s.")
        return results

    for item in addresses:
        item_label = item.get("key", "Unknown")
        item_addr = item.get("value")

        log_info(logger, f"Processing {label} - Label: {item_label}, Address: {item_addr}")

        if not item_addr or item_addr.lower() == context.web3_manager.get_zero_address():
            log_warning(logger, f"Skipping invalid or zero address for {item_label}.")
            continue

        try:
            checksum_item_addr = to_checksum_address(item_addr)
            log_info(logger, f"Checksum address: {checksum_item_addr}")

            # Fetch AVAX native token balance
            balance_wei = w3.eth.get_balance(checksum_item_addr)
            readable_balance = w3.from_wei(balance_wei, 'ether')
            log_info(logger, f"AVAX Balance for {item_label} ({checksum_item_addr}): {readable_balance}")

            results.append({
                "label": item_label,
                "address": checksum_item_addr,
                "balance": readable_balance
            })

        except Exception as e:
            log_error(logger, f"Error checking AVAX balance for {item_label} ({item_addr}): {e}")
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
        recipient_addr = to_address,
        token_symbol="AVAX",
        network="avalanche",
        amount=amount
    )

    if tx_hash == 'MfaRequired':
        messages.success(request, f"Transaction signed successfully, approval required.")
    else:
        messages.success(request, f"Transaction posted successfully with tx_hash {tx_hash}.")

    return redirect(request.path)

def avax_balances_view(request, extra_context=None):
    headers, context, csrf_token = initialize_backend_services()

    base_url = context.config_manager.get_base_url()
    w3 = context.web3_manager.get_web3_instance(network="avalanche") 

    if request.method == 'POST':
        # Delegate to the POST handler
        return handle_post_request(request, context, headers, csrf_token)

    # Collect AVAX balances
    balances = {
        "wallets": get_avax_balances(context.config_manager.get_wallet_addresses(), "Wallet", w3, context, logger),
        "parties": get_avax_balances(context.config_manager.get_party_addresses(), "Party", w3, context, logger),
    }

    transfer_funds_form = TransferFundsForm() 

    form_context = {
        "balances": balances,
        "transfer_funds_form": transfer_funds_form
    }

    if extra_context:
        form_context.update(extra_context)

    return render(request, "admin/avax_balances.html", form_context)
