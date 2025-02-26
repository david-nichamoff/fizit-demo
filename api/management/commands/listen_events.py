import logging
import time
from datetime import datetime, timezone
from eth_abi import decode

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

from django.core.management.base import BaseCommand

from api.models.event_model import Event
from api.web3 import Web3Manager
from api.config import ConfigManager
from api.registry import RegistryManager
from api.utilities.logging import log_error, log_info, log_warning

class Command(BaseCommand):
    help = 'Listen to contract events and update them in the database'

    def handle(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()
        self.w3_manager = Web3Manager()
        self.registry_manager = RegistryManager()

        # Web3 instances for both networks
        self.fizit_w3 = self.w3_manager.get_web3_instance(network="fizit")
        # self.avalanche_w3 = self.w3_manager.get_web3_instance(network="avalanche")

        # Ensure PoA middleware is applied before making any calls
        # self.avalanche_w3.middleware_onion.clear()  # Reset middleware stack to avoid duplicates
        # self.avalanche_w3.middleware_onion.add(ExtraDataToPOAMiddleware)

        # Load all contracts from config
        self.contracts = self.load_contracts()

        while True:
            try:
                # Create filters dynamically per contract type
                fizit_filters = self.create_fizit_event_filters()
                # avalanche_transfer_filter = self.create_avalanche_transfer_filter()

                # if not fizit_filters or not avalanche_transfer_filter:
                if not fizit_filters:
                    log_error(self.logger, "Failed to create one or more event filters. Retrying in 5 seconds...")
                    time.sleep(5)
                    continue

                log_info(self.logger, 'Started listening for contract events on Fizit and Avalanche networks...')

                while True:
                    try:
                        time.sleep(2)  # Pause before processing events

                        # Process events per contract type
                        for contract_type, contract_filter in fizit_filters.items():
                            self.process_fizit_events(contract_filter, contract_type)

                        # self.process_avalanche_transfer_events(avalanche_transfer_filter)

                    except Exception as e:
                        log_error(self.logger, f"Error processing events: {str(e)}")
                        break  # Exit inner loop to recreate filters

            except Exception as e:
                log_error(self.logger, f"Unexpected error: {str(e)}. Retrying in 5 seconds...")
                time.sleep(5)  # Pause before retrying

    def load_contracts(self):
        """Load all contract instances from configuration based on contract_type."""
        contracts = {}
        contract_types = self.registry_manager.get_contract_types()

        for contract_type in contract_types:
            contract_address = self.config_manager.get_contract_address(contract_type)

            if contract_address:
                contract_instance = self.fizit_w3.eth.contract(
                    address=Web3.to_checksum_address(contract_address),
                    abi=self.config_manager.get_contract_abi(contract_type)  # Ensure ABI is loaded correctly
                )
                contracts[contract_type] = contract_instance
            else:
                log_warning(self.logger, f"Skipping contract {contract_type} (no address found)")

        log_info(self.logger, f"Loaded {len(contracts)} contract instances: {list(contracts.keys())}")
        return contracts

    def create_fizit_event_filters(self):
        """Create event filters for each contract type on the Fizit network."""
        filters = {}
        for contract_type, contract_instance in self.contracts.items():
            try:
                event_signature = "ContractEvent(uint256,string,string)"
                event_topic = Web3.keccak(text=event_signature).hex()

                if not event_topic.startswith("0x"):
                    event_topic = "0x" + event_topic

                filters[contract_type] = self.fizit_w3.eth.filter({
                    'fromBlock': 'latest',
                    'address': contract_instance.address,
                    'topics': [event_topic]
                })
                log_info(self.logger, f"Created event filter for contract type '{contract_type}' at {contract_instance.address}")

            except ValueError as e:
                log_error(self.logger, f"Error creating event filter for '{contract_type}': {e}")

        return filters

    def create_avalanche_transfer_filter(self):
        """Create a filter for ERC-20 transfer events on the Avalanche network."""
        try:
            transfer_signature = Web3.keccak(text="Transfer(address,address,uint256)").hex()
            if not transfer_signature.startswith("0x"):
                transfer_signature = f"0x{transfer_signature}"

            party_addresses = [
                Web3.to_checksum_address(addr["value"])
                for addr in self.config_manager.get_party_addresses()
            ]

            token_addresses = [
                Web3.to_checksum_address(addr["value"])
                for addr in self.config_manager.get_token_addresses()
            ]

            padded_party_addresses = [
                Web3.to_hex(Web3.to_bytes(hexstr=addr).rjust(32, b'\x00'))
                for addr in party_addresses
            ]

            filter_obj = {
                'fromBlock': 'latest',
                'address': token_addresses if len(token_addresses) > 1 else token_addresses[0],
                'topics': [
                    transfer_signature,
                    padded_party_addresses,
                    padded_party_addresses
                ]
            }

            return self.avalanche_w3.eth.filter(filter_obj)

        except ValueError as e:
            log_error(self.logger, f"Error creating Avalanche transfer filter: {e}")
            return None

    def process_fizit_events(self, event_filter, contract_type):
        """Process events for a specific contract type on the Fizit network."""
        for event in event_filter.get_new_entries():
            try:
                log_info(self.logger, f"Fizit event found for {contract_type}: {event}")

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

                time.sleep(1)

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
                    existing_event.contract_type = contract_type  # New field
                    existing_event.save()
                    log_info(self.logger, f'Updated Fizit event for {contract_type}: tx_hash={tx_hash}')
                else:
                    log_warning(self.logger, f"No matching Event found for Fizit tx_hash={tx_hash}")

            except Exception as e:
                log_error(self.logger, f"Error processing Fizit event for {contract_type}: {str(e)}")

    def process_avalanche_transfer_events(self, transfer_filter):
        """Process ERC-20 Transfer events on the Avalanche network."""
        for event in transfer_filter.get_new_entries():
            try:
                log_info(self.logger, f"Avalanche transfer event found: {event}")

                tx_hash = event.get('transactionHash', b'').hex()
                if tx_hash.startswith("0x"):
                    tx_hash = tx_hash[2:]

                token_addr = event.get('address', 'Unknown token address')
                block_number = event.get('blockNumber', 'Unknown block')

                from_addr = Web3.to_checksum_address("0x" + event['topics'][1].hex()[-40:])
                to_addr = Web3.to_checksum_address("0x" + event['topics'][2].hex()[-40:])

                value = int(event['data'].hex(), 16)

                receipt = self.avalanche_w3.eth.get_transaction_receipt(tx_hash)
                gas_used = receipt.get("gasUsed") if receipt else None

                block_data = self.avalanche_w3.eth.get_block(block_number)
                # Handle both object and dictionary formats
                block_timestamp = block_data.get("timestamp") or block_data.get("time")

                details = f"Transfer {value}, token: {token_addr}"

                existing_event = Event.objects.filter(tx_hash=tx_hash).first()
                if existing_event:
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

            except Exception as e:
                log_error(self.logger, f"Error processing Avalanche transfer event: {str(e)}")