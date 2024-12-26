from django.shortcuts import render
from api.managers import ConfigManager, Web3Manager
from eth_utils import to_checksum_address
import logging

logger = logging.getLogger(__name__)

ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

def fizit_balances_view(request, extra_context=None):
    """
    Custom view to view native FIZIT balances.
    """
    try:
        logger.info("FIZIT Balances view accessed")
        
        # Initialize Config and Web3 managers
        config_manager = ConfigManager()
        web3_manager = Web3Manager()

        # Load configurations
        config = config_manager.load_config()
        w3 = web3_manager.get_web3_instance(network="fizit")  # Adjust network name as needed

        # Collect FIZIT balances
        balances = {
            "wallets": _get_fizit_balances(config_manager, "wallet_addr", "Wallet", w3, logger),
            "parties": _get_fizit_balances(config_manager, "party_addr", "Party", w3, logger),
        }

        if not balances["wallets"] and not balances["parties"]:
            logger.warning("No balances found for wallets or parties.")
            context = {"balances": {}, "error": "No balances found."}
        else:
            context = {"balances": balances}

        # Merge with extra_context if provided
        if extra_context:
            context.update(extra_context)

        # Render the template
        return render(request, "admin/fizit_balances.html", context)

    except Exception as e:
        logger.error(f"Error in fizit_balances_view: {e}")
        return render(
            request,
            "admin/fizit_balances.html",
            {"error": f"An error occurred: {str(e)}"},
            status=500,
        )

def _get_fizit_balances(config_manager, key, label, w3, logger):
    """Helper to retrieve FIZIT native token balances for wallets or parties."""
    addresses = config_manager.get_config_value(key)
    results = []

    if not addresses:
        logger.warning(f"No addresses found for key '{key}'.")
        return results

    for item in addresses:
        item_label = item.get("key", "Unknown")
        item_addr = item.get("value")
        logger.info(f"Processing {label} - Label: {item_label}, Address: {item_addr}")

        if not item_addr or item_addr.lower() == ZERO_ADDRESS:
            logger.warning(f"Skipping invalid or zero address for {item_label}.")
            continue

        try:
            checksum_item_addr = to_checksum_address(item_addr)
            logger.info(f"Checksum address: {checksum_item_addr}")

            # Fetch FIZIT native token balance
            balance_wei = w3.eth.get_balance(checksum_item_addr)
            readable_balance = w3.from_wei(balance_wei, 'ether')
            logger.info(f"FIZIT Balance for {item_label} ({checksum_item_addr}): {readable_balance}")

            results.append({"label": item_label, "address": checksum_item_addr, "balance": readable_balance})
        except Exception as e:
            logger.error(f"Error checking FIZIT balance for {item_label} ({item_addr}): {e}")
            results.append({"label": item_label, "address": item_addr, "balance": "Error"})

    return results