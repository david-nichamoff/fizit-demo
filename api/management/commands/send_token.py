import logging
from decimal import Decimal
from django.core.management.base import BaseCommand
from eth_utils import to_checksum_address
from api.managers import ConfigManager, SecretsManager, Web3Manager

from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware

class Command(BaseCommand):
    help = 'Send tokens (native or ERC-20) between wallet addresses.'

    def add_arguments(self, parser):
        parser.add_argument('--from_addr', type=str, required=True, help='The sender wallet address.')
        parser.add_argument('--to_addr', type=str, required=True, help='The recipient wallet address.')
        parser.add_argument('--amount', type=Decimal, required=True, help='The amount of token to send.')
        parser.add_argument('--token', type=str, required=True, help='The token to send (e.g., avax, fizit, or ERC-20 token name).')

    def handle(self, *args, **kwargs):
        from_addr = kwargs['from_addr']
        to_addr = kwargs['to_addr']
        amount = kwargs['amount']
        token = kwargs['token'].lower()

        # Initialize Config, Secrets, and Web3Manager
        self._initialize(token)

        try:
            if token == "avax":
                self._send_native_token(from_addr, to_addr, amount, "AVAX")
            elif token == "fizit":
                self._send_native_token(from_addr, to_addr, amount, "FIZIT")
            else:
                self._send_erc20_token(from_addr, to_addr, amount, token)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error: {str(e)}"))

    def _initialize(self, token):
        """Initialize ConfigManager, SecretsManager, and Web3Manager."""
        self.logger = logging.getLogger(__name__)

        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()

        self.secrets_manager = SecretsManager()
        self.keys = self.secrets_manager.load_keys()

        # Determine the network based on the token
        if token.lower() == "avax":
            self.network = "avalanche"
        elif token.lower() == "fizit":
            self.network = "fizit"
        else:
            # Handle ERC-20 tokens
            token_config = next((t for t in self.config_manager.get_config_value("token_addr") if t["key"].lower() == token.lower()), None)
            if not token_config:
                raise ValueError(f"Unsupported token: {token}")
            self.token_address = token_config["value"]
            self.network = "avalanche"

        # Initialize Web3Manager for the determined network
        self.w3_manager = Web3Manager()
        self.w3 = self.w3_manager.get_web3_instance(network=self.network)

        # Inject middleware for POA chains if necessary
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    def _send_native_token(self, from_addr, to_addr, amount, token_name):
        """Send native token (AVAX or FIZIT)."""
        try:
            checksum_from_addr = to_checksum_address(from_addr)
            checksum_to_addr = to_checksum_address(to_addr)
            value = self.w3.to_wei(amount, 'ether')

            # Build and send transaction
            transaction = {
                'from': checksum_from_addr,
                'to': checksum_to_addr,
                'value': value,
                'gas': 21000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(checksum_from_addr),
            }

            tx_receipt = self.w3_manager.send_signed_transaction(transaction, from_addr, None, self.network)
            if tx_receipt["status"] == 1:
                self.stdout.write(self.style.SUCCESS(f"Successfully sent {amount} {token_name} from {from_addr} to {to_addr}. Transaction hash: {tx_receipt['transactionHash'].hex()}"))
            else:
                raise RuntimeError(f"Transaction failed with status: {tx_receipt['status']}")
        except Exception as e:
            self.logger.error(f"Error sending native token: {str(e)}")
            raise RuntimeError(f"Error sending native token: {str(e)}")

    def _send_erc20_token(self, from_addr, to_addr, amount, token):
        """Send ERC-20 token."""
        try:
            # Get token details from configuration
            tokens = self.config_manager.get_config_value("token_addr")
            token_details = next((t for t in tokens if t["key"].lower() == token), None)

            if not token_details:
                raise ValueError(f"Token '{token}' not found in configuration.")

            token_addr = token_details["value"]
            token_contract = self.w3.eth.contract(
                address=to_checksum_address(token_addr),
                abi=[
                    {
                        "constant": False,
                        "inputs": [
                            {"name": "_to", "type": "address"},
                            {"name": "_value", "type": "uint256"}
                        ],
                        "name": "transfer",
                        "outputs": [{"name": "", "type": "bool"}],
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
            )

            # Try to get token decimals; default to 18 if not found
            try:
                decimals = token_contract.functions.decimals().call()
            except Exception as e:
                self.logger.warning(f"Could not retrieve decimals for token '{token}'. Defaulting to 18. Error: {str(e)}")
                decimals = 18  # Default to 18 decimals if the function is not available

            value = int(amount * (10 ** decimals))

            # Build transaction
            checksum_from_addr = to_checksum_address(from_addr)
            checksum_to_addr = to_checksum_address(to_addr)

            transaction = token_contract.functions.transfer(
                checksum_to_addr, value
            ).build_transaction({
                'from': checksum_from_addr,
                'gas': 100000,  # Adjust gas limit if necessary
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(checksum_from_addr),
            })

            # Send transaction
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, from_addr, None, self.network)
            if tx_receipt["status"] == 1:
                self.stdout.write(self.style.SUCCESS(f"Successfully sent {amount} {token.upper()} from {from_addr} to {to_addr}. Transaction hash: {tx_receipt['transactionHash'].hex()}"))
            else:
                raise RuntimeError(f"Transaction failed with status: {tx_receipt['status']}")
        except Exception as e:
            self.logger.error(f"Error sending ERC-20 token: {str(e)}")
            raise RuntimeError(f"Error sending ERC-20 token: {str(e)}")