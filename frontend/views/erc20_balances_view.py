import logging
from eth_utils import to_checksum_address
from django.shortcuts import render
from api.config import ConfigManager
from api.web3 import Web3Manager
from api.utilities.logging import log_info, log_warning, log_error

logger = logging.getLogger(__name__)

ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

def erc20_balances_view(request, extra_context=None):
    """
    Custom view to view ERC-20 token balances.
    """
    try:
        log_info(logger, "ERC-20 Balances view accessed")

        # Initialize Config and Web3 managers
        config_manager = ConfigManager()
        web3_manager = Web3Manager()
        w3 = web3_manager.get_web3_instance(network="avalanche")  # Adjust network if needed

        # Get requested token
        token_name = request.GET.get("token", "USDC").lower()
        token_list = config_manager.get_token_addresses()
        token = next((t for t in token_list if t["key"].lower() == token_name), None)

        if not token:
            log_error(logger, f"Token '{token_name}' not found in configuration.")
            return render(
                request,
                "admin/erc20_balances.html",
                {"error": f"Token '{token_name}' not configured."},
                status=404,
            )

        token_address = to_checksum_address(token["value"])  # Ensure checksum format
        token_abi = _get_erc20_abi()

        # Collect balances for wallets and parties
        balances = {
            "wallets": _get_balances(config_manager.get_wallet_addresses(), "Wallet", token_name, token_address, token_abi, w3, logger),
            "parties": _get_balances(config_manager.get_party_addresses(), "Party", token_name, token_address, token_abi, w3, logger),
        }

        if not balances["wallets"] and not balances["parties"]:
            log_warning(logger, "No balances found for wallets or parties.")
            context = {"balances": {}, "token_name": token_name, "error": "No balances found."}
        else:
            context = {"balances": balances, "token_name": token_name}

        # Merge with extra_context if provided
        if extra_context:
            context.update(extra_context)

        return render(request, "admin/erc20_balances.html", context)

    except Exception as e:
        log_error(logger, f"Error in erc20_balances_view: {e}")
        return render(
            request,
            "admin/erc20_balances.html",
            {"error": f"An error occurred: {str(e)}"},
            status=500,
        )

def _get_balances(addresses, label, token_name, token_address, token_abi, w3, logger):
    """Helper to retrieve ERC-20 balances for wallets or parties."""
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

            # Fetch balance from ERC-20 contract
            token_contract = w3.eth.contract(address=token_address, abi=token_abi)
            balance = token_contract.functions.balanceOf(checksum_item_addr).call()
            decimals = token_contract.functions.decimals().call()
            readable_balance = balance / (10 ** decimals)

            log_info(logger, f"{token_name.upper()} Balance for {item_label} ({checksum_item_addr}): {readable_balance}")

            results.append({"label": item_label, "address": checksum_item_addr, "balance": readable_balance})
        except Exception as e:
            log_error(logger, f"Error checking {token_name.upper()} balance for {item_label} ({item_addr}): {e}")
            results.append({"label": item_label, "address": item_addr, "balance": "Error"})

    return results

def _get_erc20_abi():
    """Minimal ERC-20 ABI for balance and decimals functions."""
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