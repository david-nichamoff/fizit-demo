import os
from django.core.management.base import BaseCommand
from django.conf import settings
from web3 import Web3
from api.managers import ConfigManager, SecretsManager

class Command(BaseCommand):
    help = 'Check the current native token (FIZIT) balance of specified addresses from the configuration'

    def handle(self, *args, **kwargs):
        # Initialize Config and Secrets
        self._initialize_config()

        # Retrieve balances for the specified addresses
        contract_wallet_balance = self._get_native_token_balance(self.config['contract_wallet_addr'])
        transactor_wallet_balance = self._get_native_token_balance(self.config['transactor_wallet_addr'])
        operations_wallet_balance = self._get_native_token_balance(self.config['operations_wallet_addr'])
        treasury_wallet_balance = self._get_native_token_balance(self.config['treasury_wallet_addr'])
        admin_wallet_balance = self._get_native_token_balance(self.config['admin_wallet_addr'])

        # Log or display the balances
        self.stdout.write(self.style.SUCCESS(f'Contract Wallet Balance: {contract_wallet_balance} FIZIT'))
        self.stdout.write(self.style.SUCCESS(f'Transactor Wallet Balance: {transactor_wallet_balance} FIZIT'))
        self.stdout.write(self.style.SUCCESS(f'Operations Wallet Balance: {operations_wallet_balance} FIZIT'))
        self.stdout.write(self.style.SUCCESS(f'Treasury Wallet Balance: {treasury_wallet_balance} FIZIT'))
        self.stdout.write(self.style.SUCCESS(f'Admin Wallet Balance: {admin_wallet_balance} FIZIT'))

    def _initialize_config(self):
        # Initialize SecretsManager and ConfigManager to load keys and config
        self.secrets_manager = SecretsManager()
        self.config_manager = ConfigManager()

        # Load the keys and config from the respective managers
        self.keys = self.secrets_manager.load_keys()
        self.config = self.config_manager.load_config()

        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.config['ava_rpc']))
        if not self.w3.is_connected():
            self.stdout.write(self.style.ERROR("Failed to connect to the blockchain"))
            raise ConnectionError("Unable to connect to the blockchain provider.")

    def _get_native_token_balance(self, address):
        try:
            # Convert the address to checksum format using the web3 instance
            checksum_address = self.w3.to_checksum_address(address)

            # Get the native token (FIZIT) balance in Wei (smallest unit of the token)
            balance_wei = self.w3.eth.get_balance(checksum_address)
            
            # Convert Wei to the actual FIZIT value (assuming 18 decimals like AVAX/ETH)
            balance_fizit = self.w3.from_wei(balance_wei, 'ether')
            return balance_fizit
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error retrieving balance for address {address}: {str(e)}"))
            return None