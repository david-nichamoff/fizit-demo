import logging
from django.core.management.base import BaseCommand
from api.managers import ConfigManager, SecretsManager
from api.managers.web3_manager import Web3Manager
from api.utilities.logging import log_error, log_info

class Command(BaseCommand):
    help = "Transfer FIZIT from one wallet address to another"

    def add_arguments(self, parser):
        parser.add_argument('--from_addr', type=str, required=True, help="Sender's wallet address")
        parser.add_argument('--to_addr', type=str, required=True, help="Recipient's wallet address")
        parser.add_argument('--amount', type=float, required=True, help="Amount of FIZIT to send")

    def handle(self, *args, **kwargs):
        from_addr = kwargs['from_addr']
        to_addr = kwargs['to_addr']
        amount = kwargs['amount']

        self.logger = logging.getLogger(__name__)

        # Initialize Config and Web3Manager
        self._initialize()

        try:
            log_info(self.logger, f"Initiating native FIZIT transfer: {amount} from {from_addr} to {to_addr}")

            # Convert amount to Wei (assuming FIZIT uses 18 decimals like AVAX)
            wei_amount = self.web3.to_wei(amount, 'ether')

            # Prepare transaction
            transaction = {
                "to": self.web3.to_checksum_address(to_addr),
                "value": wei_amount,
                "data": "0x",  # Empty data for native transfers
            }

            # Send the transaction using Web3Manager
            tx_receipt = self.web3_manager.send_signed_transaction(transaction, from_addr, contract_idx=None)

            # Log and display transaction hash
            log_info(self.logger, f"Transaction successful: {tx_receipt.transactionHash.hex()}")
            self.stdout.write(self.style.SUCCESS(f"✅ FIZIT transfer successful! TX Hash: {tx_receipt.transactionHash.hex()}"))

        except Exception as e:
            log_error(self.logger, f"Error during FIZIT transfer: {str(e)}")
            self.stderr.write(self.style.ERROR(f"❌ Error during transfer: {str(e)}"))

    def _initialize(self):
        """Initialize ConfigManager, SecretsManager, and Web3Manager."""
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.secrets_manager = SecretsManager()
        self.keys = self.secrets_manager.load_keys()
        self.web3_manager = Web3Manager()
        self.web3 = self.web3_manager.get_web3_instance()