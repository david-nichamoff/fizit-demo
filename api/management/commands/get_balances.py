from django.core.management.base import BaseCommand
from eth_utils import to_checksum_address
from api.managers import ConfigManager, SecretsManager, Web3Manager
import logging

class Command(BaseCommand):
    help = 'Check balances for AVAX, FIZIT, or configured ERC-20 tokens on their respective networks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--token',
            type=str,
            required=True,
            help="The token to check balances for: 'avax', 'fizit', or the ERC-20 token key in ConfigManager"
        )

    def handle(self, *args, **kwargs):
        # Get token from arguments
        token = kwargs['token'].lower()

        # Initialize Config, Secrets, and Web3Manager
        self._initialize(token)

        # Retrieve balances for wallet addresses
        self.stdout.write(self.style.SUCCESS("--- Wallet Balances ---"))
        wallets = self.config_manager.get_config_value("wallet_addr")
        if wallets:
            self._print_balances(wallets, "Wallet", token)
        else:
            self.stdout.write(self.style.WARNING("No wallet addresses found in the configuration."))

        # Retrieve balances for party addresses
        self.stdout.write(self.style.SUCCESS("\n--- Party Balances ---"))
        parties = self.config_manager.get_config_value("party_addr")
        if parties:
            self._print_balances(parties, "Party", token)
        else:
            self.stdout.write(self.style.WARNING("No party addresses found in the configuration."))

    def _initialize(self, token):
        """Initialize ConfigManager, SecretsManager, and Web3Manager based on the token."""
        self.logger = logging.getLogger(__name__)

        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()

        self.secrets_manager = SecretsManager()
        self.keys = self.secrets_manager.load_keys()

        # Determine the network based on the token
        if token == 'avax':
            self.network = 'avalanche'
        elif token == 'fizit':
            self.network = 'fizit'
        else:
            self.network = 'avalanche'  # ERC-20 tokens are on Avalanche

        # Initialize Web3Manager for the appropriate network
        self.w3_manager = Web3Manager()
        self.w3 = self.w3_manager.get_web3_instance(network=self.network)

        # Store token details for ERC-20
        if token not in ['avax', 'fizit']:
            tokens = self.config_manager.get_config_value("token_addr")
            token_config = next((t for t in tokens if t["key"] == token), None)
            if not token_config:
                raise ValueError(f"Token '{token}' not found in ConfigManager 'token_addr'.")
            self.token_address = to_checksum_address(token_config["value"])
            self.token_abi = self._get_erc20_abi()

    def _get_balance(self, address, token):
        """Retrieve the balance for the specified token and address."""
        try:
            if token == 'avax' or token == 'fizit':
                # Native token balance
                balance_wei = self.w3.eth.get_balance(address)
                return self.w3.from_wei(balance_wei, 'ether')

            # ERC-20 token balance
            token_contract = self.w3.eth.contract(address=self.token_address, abi=self.token_abi)
            balance = token_contract.functions.balanceOf(address).call()
            decimals = token_contract.functions.decimals().call()
            return balance / (10 ** decimals)

        except Exception as e:
            self.logger.error(f"Error retrieving balance for address {address}: {str(e)}")
            return None

    def _print_balances(self, addresses, label, token):
        """Print the balances for the given addresses."""
        for item in addresses:
            item_label = item.get("key", "Unknown")
            item_addr = item.get("value")
            if not item_addr or item_addr.lower() == "0x0000000000000000000000000000000000000000":
                continue

            checksum_item_addr = to_checksum_address(item_addr)
            balance = self._get_balance(checksum_item_addr, token)
            if balance is not None:
                self.stdout.write(self.style.SUCCESS(f"{label} - {item_label}: {checksum_item_addr} | Balance: {balance} {token.upper()}"))
            else:
                self.stdout.write(self.style.ERROR(f"Failed to retrieve balance for {label} - {item_label}: {checksum_item_addr}"))

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