import logging
from django.shortcuts import render
from eth_utils import to_checksum_address
from api.config import ConfigManager
from api.web3 import Web3Manager
from api.utilities.logging import log_info, log_warning, log_error

logger = logging.getLogger(__name__)

ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

def avax_balances_view(request, extra_context=None):
    """
    Custom view to display AVAX native token balances.
    """
    try:
        log_info(logger, "AVAX Balances view accessed")

        # Initialize Config and Web3 managers
        config_manager = ConfigManager()
        web3_manager = Web3Manager()
        w3 = web3_manager.get_web3_instance(network="avalanche")  

        # Collect AVAX balances
        balances = {
            "wallets": _get_avax_balances(config_manager.get_wallet_addresses(), "Wallet", w3, logger),
            "parties": _get_avax_balances(config_manager.get_party_addresses(), "Party", w3, logger),
        }

        if not balances["wallets"] and not balances["parties"]:
            log_warning(logger, "No balances found for wallets or parties.")
            context = {"balances": {}, "error": "No balances found."}
        else:
            context = {"balances": balances}

        # Merge with extra_context if provided
        if extra_context:
            context.update(extra_context)

        return render(request, "admin/avax_balances.html", context)

    except Exception as e:
        log_error(logger, f"Error in avax_balances_view: {e}")
        return render(
            request,
            "admin/avax_balances.html",
            {"error": f"An error occurred: {str(e)}"},
            status=500,
        )

def _get_avax_balances(addresses, label, w3, logger):
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