import logging

from django.shortcuts import render, redirect
from django.contrib import messages

from eth_utils import to_checksum_address

from api.config import ConfigManager
from api.web3 import Web3Manager
from api.registry import RegistryManager
from api.secrets import SecretsManager
from api.operations import CsrfOperations
from api.web3 import Web3Manager
from api.utilities.logging import log_info, log_warning, log_error

from frontend.forms import TransferFundsForm

logger = logging.getLogger(__name__)

ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

def initialize_backend_services():
    secrets_manager = SecretsManager()
    config_manager = ConfigManager()
    registry_manager = RegistryManager()
    web3_manager = Web3Manager()

    headers = {
        'Authorization': f"Api-Key {secrets_manager.get_master_key()}",
        'Content-Type': 'application/json',
    }

    csrf_ops = CsrfOperations(headers, config_manager.get_base_url())
    csrf_token = csrf_ops.get_csrf_token()

    return headers, registry_manager, config_manager, web3_manager, csrf_token


def get_avax_balances(addresses, label, w3, logger):
    """Helper to retrieve AVAX native token balances for wallets or parties."""
    results = []

    if not addresses:
        log_warning(logger, f"No addresses found for {label}s.")
        return results

    for item in addresses:
        item_label = item.get("key", "Unknown")
        item_addr = item.get("value")

        log_info(logger, f"Processing {label} - Label: {item_label}, Address: {item_addr}")

        if not item_addr or item_addr.lower() == ZERO_ADDRESS:
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

def handle_post_request(request, headers, config, csrf_token):
    from_address = request.POST.get("from_address")
    to_address = request.POST.get("to_address")
    amount = request.POST.get("amount")

    log_info(logger, f"Send {amount} from {to_address} to {from_address}")
    messages.success(request, "Transaction posted successfully.")
    return redirect(request.path)

def avax_balances_view(request, extra_context=None):
    headers, registry_manager, config_manager, web3_manager, csrf_token = initialize_backend_services()
    base_url = config_manager.get_base_url()
    w3 = web3_manager.get_web3_instance(network="avalanche") 

    if request.method == 'POST':
        # Delegate to the POST handler
        return handle_post_request(request, headers, base_url, csrf_token)

    # Collect AVAX balances
    balances = {
        "wallets": get_avax_balances(config_manager.get_wallet_addresses(), "Wallet", w3, logger),
        "parties": get_avax_balances(config_manager.get_party_addresses(), "Party", w3, logger),
    }

    transfer_funds_form = TransferFundsForm() 

    context = {
        "balances": balances,
        "transfer_funds_form": transfer_funds_form
    }

    if extra_context:
        context.update(extra_context)

    return render(request, "admin/avax_balances.html", context)
