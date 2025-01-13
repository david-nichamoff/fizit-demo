import logging
import time
from django.core.management.base import BaseCommand
from api.models.event_model import Event
from api.managers import Web3Manager, ConfigManager
from eth_abi import decode
from datetime import datetime, timezone

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

from api.utilities.logging import  log_error, log_info, log_warning

class Command(BaseCommand):
    help = 'Listen to contract events and update them in the database'

    def handle(self, *args, **kwargs):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.w3_manager = Web3Manager()

        # Web3 instances for both networks
        self.fizit_w3 = self.w3_manager.get_web3_instance(network="fizit")
        self.avalanche_w3 = self.w3_manager.get_web3_instance(network="avalanche")
        self.avalanche_w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

        self.fizit_contract = self.w3_manager.get_web3_contract(network="fizit")
        self.logger = logging.getLogger(__name__)

        while True:
            try:
                # Create or recreate filters
                fizit_filter = self.create_fizit_event_filter()
                avalanche_transfer_filter = self.create_avalanche_transfer_filter()

                if not fizit_filter or not avalanche_transfer_filter:
                    log_error(self.logger, "Failed to create one or more event filters. Retrying in 5 seconds...")
                    time.sleep(5)
                    continue

                log_info(self.logger, 'Started listening for contract events on Fizit and Avalanche networks...')

                while True:
                    try:
                        time.sleep(2)  # Pause before processing events

                        # Process events
                        self.process_fizit_events(fizit_filter)
                        self.process_avalanche_transfer_events(avalanche_transfer_filter)

                    except Exception as e:
                        log_error(self.logger, f"Error processing events: {str(e)}")
                        break  # Exit inner loop to recreate filters

            except Exception as e:
                log_error(self.logger, f"Unexpected error: {str(e)}. Retrying in 5 seconds...")
                time.sleep(5)  # Pause before retrying

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
            log_error(self.logger, f"Error creating Fizit event filter: {e}")
            return None

    def create_avalanche_transfer_filter(self):
        """Create a filter for ERC-20 transfer events on the Avalanche network for specific party addresses."""
        try:
            # Keccak hash of the ERC-20 Transfer event signature
            transfer_signature = Web3.keccak(text="Transfer(address,address,uint256)").hex()
            if not transfer_signature.startswith("0x"):
                transfer_signature = f"0x{transfer_signature}"

            # Retrieve party addresses from config
            party_addresses = [
                Web3.to_checksum_address(addr["value"])
                for addr in self.config_manager.get_config_value("party_addr")
            ]

            # Get the token addresses and ensure they are in checksum format
            token_addresses = [
                Web3.to_checksum_address(addr["value"])
                for addr in self.config_manager.get_config_value("token_addr")
            ]

            # Pad addresses to 32 bytes for topics
            padded_party_addresses = [
                Web3.to_hex(Web3.to_bytes(hexstr=addr).rjust(32, b'\x00'))
                for addr in party_addresses
            ]

            filter_obj = {
                'fromBlock': 'latest',
                'address': token_addresses if len(token_addresses) > 1 else token_addresses[0],
                'topics': [
                    transfer_signature,
                    padded_party_addresses,  # Filter for `from` addresses
                    padded_party_addresses   # Filter for `to` addresses
                ]
            }

            return self.avalanche_w3.eth.filter(filter_obj)

        except ValueError as e:
            log_error(self.logger, f"Error creating Avalanche transfer filter: {e}")
            return None

    def process_fizit_events(self, fizit_filter):
        """Process events from the Fizit network."""
        for event in fizit_filter.get_new_entries():
            try:
                log_info(self.logger, f"Fizit event found: {event}")

                tx_hash = event.get('transactionHash', b'').hex()
                if tx_hash.startswith("0x"):
                    tx_hash = tx_hash[2:]

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

                time.sleep(1)  # Make sure the database is updated

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
                    log_info(self.logger, f'Updated Fizit event: tx_hash={tx_hash}')
                else:
                    log_warning(self.logger, f"No matching Event found for Fizit tx_hash={tx_hash}")

            except Exception as e:
                log_error(self.logger, f"Error processing Fizit event: {str(e)}")

    def process_avalanche_transfer_events(self, transfer_filter):
        """Process ERC-20 Transfer events on the Avalanche network."""
        for event in transfer_filter.get_new_entries():
            try:
                log_info(self.logger, f"Avalanche transfer event found: {event}")

                tx_hash = event.get('transactionHash', b'').hex()
                if tx_hash.startswith("0x"):
                    tx_hash = tx_hash[2:]

                log_info(self.logger, f"Tx hash: {tx_hash}")

                token_addr = event.get('address', 'Unknown token address')
                block_number = event.get('blockNumber', 'Unknown block')

                # Decode the `from`, `to`, and `value` fields
                from_addr = "0x" + event['topics'][1].hex()[-40:]
                to_addr = "0x" + event['topics'][2].hex()[-40:]

                log_info(self.logger, f"From address: {from_addr}")
                log_info(self.logger, f"To address: {to_addr}")

                value = int(event['data'].hex(), 16)  # Decode `data` as a hex string and convert to int

                log_info(self.logger, f"Amount: {value}")

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
                    log_info(self.logger, f'Updated Avalanche transfer event: tx_hash={tx_hash}')

            except Exception as e:
                log_error(self.logger, f"Error processing Avalanche transfer event: {str(e)}")