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

        # Keep track of last known contract address
        self.current_contract_address = {}

        while True:
            try:
                # Load all contracts from config
                self.load_contracts()
                fizit_filters = self.create_fizit_event_filters()

                # if not fizit_filters
                if not fizit_filters:
                    log_error(self.logger, "Failed to create one or more event filters...")
                    time.sleep(self.config_manager.get_listen_sleep_time())
                    continue

                log_info(self.logger, 'Started listening for contract events on Fizit network...')

                while True:
                    try:
                        time.sleep(self.config_manager.get_listen_sleep_time())  # Pause before processing events

                        #  Check for contract config changes in the inner loop
                        if self.contracts_changed():
                            log_warning(self.logger, "Contract addresses changed! Reloading contracts and filters...")
                            break  # Exit inner loop to reload everything

                        # Process events per contract type
                        for contract_type, contract_filter in fizit_filters.items():
                            self.process_fizit_events(contract_filter, contract_type)

                    except Exception as e:
                        log_error(self.logger, f"Error processing events: {str(e)}")
                        break  # Exit inner loop to recreate filters

            except Exception as e:
                log_error(self.logger, f"Unexpected error: {str(e)}. Retrying in 5 seconds...")
                time.sleep(self.config_manager.get_listen_sleep_time())

    def contracts_changed(self):
        contract_types = self.registry_manager.get_contract_types()

        for contract_type in contract_types:
            latest_address = self.config_manager.get_contract_address(contract_type)
        
            if not latest_address:
                continue
        
            previous_address = self.current_contract_address.get(contract_type)        

            if previous_address != latest_address:
                log_info(self.logger, f"Detected contract address change for {contract_type}")
                return True

        return False

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
                self.current_contract_address[contract_type] = contract_address
            else:
                log_error(self.logger, f"Skipping contract {contract_type} (no address found)")

        self.contracts = contracts

        log_info(self.logger, f"Loaded contract: {list(contracts.keys())}")

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

    def process_fizit_events(self, event_filter, contract_type):
        """Process events for a specific contract type on the Fizit network."""
        for event in event_filter.get_new_entries():
            try:
                log_info(self.logger, f"Fizit event found for {contract_type}: {event}")

                tx_hash = event.get('transactionHash', b'').hex()
                if not tx_hash.startswith("0x"):
                    tx_hash = "0x" + tx_hash

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

                time.sleep(self.config_manager.get_listen_sleep_time())

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
                    log_error(self.logger, f"No matching Event found for Fizit tx_hash={tx_hash}")

            except Exception as e:
                log_error(self.logger, f"Error processing Fizit event for {contract_type}: {str(e)}")