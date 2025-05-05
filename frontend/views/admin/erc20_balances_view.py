import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from eth_utils import to_checksum_address

from api.adapters.bank import TokenAdapter
from api.operations import CsrfOperations
from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_info, log_warning, log_error
from frontend.forms.admin import TransferFundsForm

logger = logging.getLogger(__name__)

def _initialize_backend_services():
    context = build_app_context()
    headers = {
        'Authorization': f"Api-Key {context.secrets_manager.get_master_key()}",
        'Content-Type': 'application/json',
    }

    csrf_token = CsrfOperations(headers, context.config_manager.get_base_url()).get_csrf_token()
    return headers, context, csrf_token

def _get_balances_for_token(w3, token_address, token_abi, addresses, label, token_name, context):
    results = []
    for item in addresses:
        item_label = item.get("key", "Unknown")
        item_addr = item.get("value")
        if not item_addr or item_addr.lower() == context.web3_manager.get_zero_address():
            continue
        try:
            checksum = to_checksum_address(item_addr)
            contract = w3.eth.contract(address=token_address, abi=token_abi)
            balance = contract.functions.balanceOf(checksum).call()
            decimals = contract.functions.decimals().call()
            readable_balance = balance / (10 ** decimals)
            results.append({"label": item_label, "address": checksum, "balance": readable_balance})
        except Exception as e:
            log_error(logger, f"Error retrieving balance for {item_label}: {e}")
            results.append({"label": item_label, "address": item_addr, "balance": "Error"})
    return results

def get_erc20_abi():
    return [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function",
        },
    ]

def handle_post_request(request, context, headers, csrf_token):
    try:
        # Extract form data
        token_combo = request.POST.get("token_symbol")  # format: "network:token"
        network, token_symbol = token_combo.split(":")
        from_address = request.POST.get("from_address")
        to_address = request.POST.get("to_address")
        amount = request.POST.get("amount")

        log_info(logger, f"POST: Transfer {amount} {token_symbol} from {from_address} to {to_address} on {network}")

        # Create TokenAdapter with context
        token_adapter = TokenAdapter(context)

        # Make payment
        tx_hash = token_adapter.make_payment(
            contract_type=None,
            contract_idx=None,
            funder_addr=from_address,
            recipient_addr=to_address,
            network=network,
            token_symbol=token_symbol,
            amount=amount
        )

        messages.success(request, f"Transaction posted successfully with tx_hash {tx_hash}")
        return redirect(request.path)

    except Exception as e:
        log_error(logger, f"Error processing transfer: {e}")
        messages.error(request, f"Failed to process transaction: {str(e)}")
        return redirect(request.path)

def erc20_balances_view(request, extra_context=None):
    headers, context, csrf_token = _initialize_backend_services()
    token_config = context.config_manager.get_all_token_addresses() 
    log_info(logger, f"Loaded token config: {token_config}" )

    if request.method == 'POST':
        return handle_post_request(request, context, headers, csrf_token)

    balances = {}
    token_abi = get_erc20_abi()

    for network_entry in token_config:
        network = network_entry["key"]
        tokens = network_entry.get("value", [])

        try:
            w3 = context.web3_manager.get_web3_instance(network)
        except Exception as e:
            log_warning(logger, f"Skipping network '{network}' due to error: {e}")
            continue

        balances[network] = {}

        for token_entry in tokens:
            token_name = token_entry["key"]
            token_addr = to_checksum_address(token_entry["value"])
            log_info(logger, f"Fetching balances for {token_name} on {network}")

            wallets = _get_balances_for_token(w3, token_addr, token_abi, context.config_manager.get_wallet_addresses(), "Wallet", token_name, context)
            parties = _get_balances_for_token(w3, token_addr, token_abi, context.config_manager.get_party_addresses(), "Party", token_name, context)

            balances[network][token_name] = {
                "wallets": wallets,
                "parties": parties
            }

    # Prepare token symbols per network for the form
    token_choices = []
    for entry in token_config:
        net = entry["key"]
        for token in entry.get("value", []):
            symbol = token["key"]
            label = f"{symbol.upper()} ({net})"
            value = f"{net}:{symbol}"
            token_choices.append((value, label))

    transfer_funds_form = TransferFundsForm()
    transfer_funds_form.fields["token_symbol"].choices = token_choices

    context_data = {
        "balances": balances,
        "transfer_funds_form": transfer_funds_form,
    }

    if extra_context:
        context_data.update(extra_context)

    return render(request, "admin/erc20_balances.html", context_data)