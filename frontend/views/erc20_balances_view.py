from django.shortcuts import render
from api.managers import ConfigManager, Web3Manager
from eth_utils import to_checksum_address
import logging

logger = logging.getLogger(__name__)

ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

def erc20_balances_view(request, extra_context=None):
    """
    Custom view to view ERC-20 token balances.
    """
    try:
        logger.info("ERC-20 Balances view accessed")
        
        # Initialize Config and Web3 managers
        config_manager = ConfigManager()
        web3_manager = Web3Manager()

        # Load configurations
        config = config_manager.load_config()
        w3 = web3_manager.get_web3_instance(network="avalanche")  # Adjust network if needed

        # Token details
        token_name = request.GET.get("token", "usdc").lower()
        tokens = config_manager.get_config_value("token_addr")
        token = next((t for t in tokens if t["key"] == token_name), None)

        if not token:
            logger.error(f"Token '{token_name}' not found in configuration.")
            return render(
                request,
                "admin/erc20_balances.html",
                {"error": f"Token '{token_name}' not configured."},
                status=404,
            )

        token_address = token["value"]
        token_abi = _get_erc20_abi()

        # Collect balances
        balances = {
            "wallets": _get_balances(config_manager, "wallet_addr", "Wallet", token_name, token_address, token_abi, w3, logger),
            "parties": _get_balances(config_manager, "party_addr", "Party", token_name, token_address, token_abi, w3, logger),
        }

        if not balances["wallets"] and not balances["parties"]:
            logger.warning("No balances found for wallets or parties.")
            context = {"balances": {}, "token_name": token_name, "error": "No balances found."}
        else:
            context = {"balances": balances, "token_name": token_name}

        # Merge with extra_context if provided
        if extra_context:
            context.update(extra_context)

        # Render the template
        return render(request, "admin/erc20_balances.html", context)

    except Exception as e:
        logger.error(f"Error in erc20_balances_view: {e}")
        return render(
            request,
            "admin/erc20_balances.html",
            {"error": f"An error occurred: {str(e)}"},
            status=500,
        )

def _get_balances(config_manager, key, label, token_name, token_address, token_abi, w3, logger):
    """Helper to retrieve ERC-20 balances for wallets or parties."""
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

            # Fetch balance from ERC-20 contract
            checksum_token_address = to_checksum_address(token_address)
            token_contract = w3.eth.contract(address=checksum_token_address, abi=token_abi)
            balance = token_contract.functions.balanceOf(checksum_item_addr).call()
            decimals = token_contract.functions.decimals().call()
            readable_balance = balance / (10 ** decimals)
            logger.info(f"Balance for {item_label} ({checksum_item_addr}): {readable_balance}")

            results.append({"label": item_label, "address": checksum_item_addr, "balance": readable_balance})
        except Exception as e:
            logger.error(f"Error checking balance for {item_label} ({item_addr}): {e}")
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