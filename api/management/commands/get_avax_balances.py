from django.core.management.base import BaseCommand
from eth_utils import to_checksum_address
from api.managers import ConfigManager, SecretsManager, Web3Manager
import logging

class Command(BaseCommand):
    help = 'Check the current native token (AVAX) balance of all wallet addresses from the configuration using the Avalanche RPC'

    def handle(self, *args, **kwargs):
        # Initialize Config, Secrets, and Web3Manager
        self._initialize()

        # Retrieve balances for all wallet addresses in the configuration
        wallets = self.config_manager.get_config_value("wallet_addr")
        if not wallets:
            self.stdout.write(self.style.WARNING("No wallets found in the configuration."))
            return

        for wallet in wallets:
            wallet_label = wallet.get("key", "Unknown")
            wallet_addr = wallet.get("value")
            if wallet_addr:
                checksum_wallet_addr = to_checksum_address(wallet_addr)
                balance = self._get_native_balance(checksum_wallet_addr)
                if balance is not None:
                    self.stdout.write(self.style.SUCCESS(f"{wallet_label} balance: {balance} AVAX"))
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to retrieve balance for {wallet_label}"))
            else:
                self.stdout.write(self.style.ERROR(f"Wallet address missing for {wallet_label}"))

    def _initialize(self):
        """Initialize ConfigManager, SecretsManager, and Web3Manager for Avalanche RPC."""
        self.logger = logging.getLogger(__name__)
        
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        
        self.secrets_manager = SecretsManager()
        self.keys = self.secrets_manager.load_keys()

        # Initialize Web3Manager for the Avalanche network
        self.w3_manager = Web3Manager()
        self.w3 = self.w3_manager.get_web3_instance(network="avalanche")

    def _get_native_balance(self, address):
        try:
            # Get the native token (AVAX) balance in Wei (smallest unit of the token)
            balance_wei = self.w3.eth.get_balance(address)

            # Convert Wei to the actual AVAX value (assuming 18 decimals like AVAX/ETH)
            balance_avax = self.w3.from_wei(balance_wei, 'ether')
            return balance_avax

        except Exception as e:
            self.logger.error(f"Error retrieving balance for address {address}: {str(e)}")
            return None