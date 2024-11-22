import logging
from django.core.management.base import BaseCommand
from eth_utils import to_checksum_address
from api.managers import ConfigManager, SecretsManager, Web3Manager

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check the current ERC-20 token balances of all wallet addresses for all tokens in the configuration on the Avalanche C-Chain'

    def handle(self, *args, **kwargs):
        # Initialize Config, Secrets, and Web3Manager
        self._initialize()

        # Retrieve the token addresses from configuration
        tokens = self.config_manager.get_config_value("token_addr")
        if not tokens:
            self.stdout.write(self.style.ERROR("No ERC-20 tokens configured in 'token_addr'."))
            return

        # Retrieve wallet addresses from configuration
        wallets = self.config_manager.get_config_value("party_addr")
        if not wallets:
            self.stdout.write(self.style.WARNING("No wallets found in the configuration."))
            return

        for token in tokens:
            token_symbol = token.get("key")
            token_addr = token.get("value")
            if not token_addr:
                self.stdout.write(self.style.ERROR(f"Token address for {token_symbol} is missing or invalid."))
                continue

            self.stdout.write(self.style.SUCCESS(f"Checking balances for token: {token_symbol} ({token_addr})"))

            for wallet in wallets:
                wallet_label = wallet.get("key", "Unknown")
                wallet_addr = wallet.get("value")
                if wallet_addr:
                    checksum_wallet_addr = to_checksum_address(wallet_addr)
                    balance = self._get_erc20_balance(checksum_wallet_addr, token_addr)
                    if balance is not None:
                        self.stdout.write(self.style.SUCCESS(f"{wallet_label} balance: {balance} {token_symbol}"))
                    else:
                        self.stdout.write(self.style.ERROR(f"Failed to retrieve balance for {wallet_label} ({token_symbol})"))
                else:
                    self.stdout.write(self.style.ERROR(f"Wallet address missing for {wallet_label}"))

    def _initialize(self):
        """Initialize ConfigManager, SecretsManager, and Web3Manager."""
        self.logger = logging.getLogger(__name__)
        
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        
        self.secrets_manager = SecretsManager()
        self.keys = self.secrets_manager.load_keys()

        # Initialize Web3Manager for the Avalanche network
        self.w3_manager = Web3Manager()
        self.w3 = self.w3_manager.get_web3_instance(network="avalanche")

    def _get_erc20_balance(self, address, token_addr):
        """Retrieve the ERC-20 token balance of a wallet."""
        try:
            token_contract = self.w3.eth.contract(
                address=to_checksum_address(token_addr), 
                abi=self._get_erc20_abi()
            )

            # Get the token balance
            balance = token_contract.functions.balanceOf(address).call()

            # Get the token decimals for formatting
            decimals = token_contract.functions.decimals().call()

            # Format the balance based on decimals
            formatted_balance = balance / (10 ** decimals)
            return formatted_balance

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error retrieving balance for address {address}: {str(e)}"))
            return None

    def _get_erc20_abi(self):
        """Return the minimal ABI for ERC-20 tokens."""
        return [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            }
        ]