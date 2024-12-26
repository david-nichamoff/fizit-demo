import logging
import time
from django.core.management.base import BaseCommand
from api.models.event_model import Event
from api.managers import Web3Manager, ConfigManager
from eth_abi import decode
from datetime import datetime, timezone

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

class Command(BaseCommand):
    help = 'Listen to contract events and update them in the database'

    def handle(self, *args, **kwargs):
        # Initialize components
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.w3_manager = Web3Manager()

        # Web3 instances for both networks
        self.fizit_w3 = self.w3_manager.get_web3_instance(network="fizit")
        self.avalanche_w3 = self.w3_manager.get_web3_instance(network="avalanche")
        self.avalanche_w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

        # Contract instance for Fizit network
        self.fizit_contract = self.w3_manager.get_web3_contract(network="fizit")

        self.logger = logging.getLogger(__name__)

        # Create event filters
        fizit_filter = self.create_fizit_event_filter()
        avalanche_transfer_filter = self.create_avalanche_transfer_filter()

        if not fizit_filter or not avalanche_transfer_filter:
            self.logger.error("Failed to create one or more event filters. Exiting...")
            return

        self.logger.info('Started listening for contract events on Fizit and Avalanche networks...')

        while True:
            try:
                # Process Fizit events
                self.process_fizit_events(fizit_filter)

                # Process Avalanche transfer events
                self.process_avalanche_transfer_events(avalanche_transfer_filter)

                time.sleep(2)  # Pause to avoid excessive polling

            except Exception as e:
                self.logger.error(f"Unexpected error: {str(e)}")
                self.stdout.write(self.style.ERROR(f"Unexpected error: {str(e)}"))

    def create_fizit_event_filter(self):
        """Create a filter for contract events on the Fizit network."""
        try:
            event_signature = "ContractEvent(uint256,string,string)"
            event_topic = Web3.keccak(text=event_signature).hex()

            # Ensure the event topic has the 0x prefix
            if not event_topic.startswith("0x"):
                event_topic = "0x" + event_topic

            return self.fizit_w3.eth.filter({
                'fromBlock': 'latest',
                'address': self.fizit_contract.address,
                'topics': [event_topic]
            })
        except ValueError as e:
            self.logger.error(f"Error creating Fizit event filter: {e}")
            return None

    def create_avalanche_transfer_filter(self):
        """Create a filter for ERC-20 transfer events on the Avalanche network."""
        try:
            # Keccak hash of the ERC-20 Transfer event signature
            transfer_signature = Web3.keccak(text="Transfer(address,address,uint256)").hex()
            if not transfer_signature.startswith("0x"):
                transfer_signature = f"0x{transfer_signature}"

            # Get the token addresses and ensure they are in checksum format
            token_addresses = [token['value'] for token in self.config_manager.get_config_value("token_addr")]
            checksum_addresses = [
                Web3.to_checksum_address(addr) if not Web3.is_checksum_address(addr) else addr
                for addr in token_addresses
            ]

            # Construct the filter object
            filter_obj = {
                'fromBlock': 'latest',
                'address': checksum_addresses[0] if len(checksum_addresses) == 1 else checksum_addresses,
                'topics': [transfer_signature]
            }

            # Create the filter
            return self.avalanche_w3.eth.filter(filter_obj)

        except ValueError as e:
            self.logger.error(f"Error creating Avalanche transfer filter: {e}")
            return None

    def process_fizit_events(self, fizit_filter):
        """Process events from the Fizit network."""
        for event in fizit_filter.get_new_entries():
            try:
                self.logger.info(f"Fizit event found: {event}")

                tx_hash = event.get('transactionHash', b'').hex()
                if not tx_hash.startswith("0x"):
                    tx_hash = f"0x{tx_hash}"

                contract_addr = event.get('address', 'Unknown address')
                block_number = event.get('blockNumber', 'Unknown block')
                contract_idx = int(event['topics'][1].hex(), 16)

                data = event['data']
                decoded_data = decode(['string', 'string'], bytes(data))
                event_type = decoded_data[0]
                details = decoded_data[1]

                receipt = self.fizit_w3.eth.get_transaction_receipt(tx_hash)
                gas_used = receipt.get("gasUsed") if receipt else None
                block_timestamp = self.fizit_w3.eth.get_block(block_number).timestamp

                existing_event = Event.objects.filter(tx_hash=tx_hash).first()
                if existing_event:
                    existing_event.contract_idx = contract_idx
                    existing_event.contract_addr = contract_addr
                    existing_event.event_type = event_type
                    existing_event.details = details
                    existing_event.event_dt = datetime.fromtimestamp(block_timestamp, tz=timezone.utc)
                    existing_event.gas_used = gas_used
                    existing_event.status = "complete"
                    existing_event.network = "fizit"
                    existing_event.save()
                    self.logger.info(f'Updated Fizit event: tx_hash={tx_hash}')
                else:
                    self.logger.warning(f"No matching Event found for Fizit tx_hash={tx_hash}")

            except Exception as e:
                self.logger.error(f"Error processing Fizit event: {str(e)}")

    def process_avalanche_transfer_events(self, transfer_filter):
        """Process ERC-20 Transfer events on the Avalanche network."""
        for event in transfer_filter.get_new_entries():
            try:
                self.logger.info(f"Avalanche transfer event found: {event}")

                tx_hash = event.get('transactionHash', b'').hex()
                if not tx_hash.startswith("0x"):
                    tx_hash = f"0x{tx_hash}"

                token_addr = event.get('address', 'Unknown token address')
                block_number = event.get('blockNumber', 'Unknown block')

                # Decode the `from`, `to`, and `value` fields
                from_addr = "0x" + event['topics'][1].hex()[-40:]
                to_addr = "0x" + event['topics'][2].hex()[-40:]
                value = int(event['data'].hex(), 16)  # Decode `data` as a hex string and convert to int

                # Get transaction receipt and block timestamp
                receipt = self.avalanche_w3.eth.get_transaction_receipt(tx_hash)
                gas_used = receipt.get("gasUsed") if receipt else None
                block_timestamp = self.avalanche_w3.eth.get_block(block_number).timestamp

                details = f"Transfer {value}, token: {token_addr}"

                # Fetch the existing event based on tx_hash
                existing_event = Event.objects.filter(tx_hash=tx_hash).first()
                if existing_event:
                    # Update the existing event
                    existing_event.contract_addr = token_addr
                    existing_event.event_type = "ERC-20 Transfer"
                    existing_event.details = details
                    existing_event.from_addr = from_addr
                    existing_event.to_addr = to_addr
                    existing_event.event_dt = datetime.fromtimestamp(block_timestamp, tz=timezone.utc)
                    existing_event.gas_used = gas_used
                    existing_event.status = "complete"
                    existing_event.network = "avalanche"
                    existing_event.save()
                    self.logger.info(f'Updated Avalanche transfer event: tx_hash={tx_hash}')

            except Exception as e:
                self.logger.error(f"Error processing Avalanche transfer event: {str(e)}")