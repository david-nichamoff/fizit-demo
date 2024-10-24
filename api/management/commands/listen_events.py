import logging
import time
from django.core.management.base import BaseCommand
from api.models.event_models import Event
from api.managers import Web3Manager, ConfigManager
from eth_abi import decode

from web3 import Web3

class Command(BaseCommand):
    help = 'Listen to contract events and store them in the database'

    def handle(self, *args, **kwargs):
        # Initialize components
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.w3_manager = Web3Manager()
        self.w3 = self.w3_manager.get_web3_instance()
        self.w3_contract = self.w3_manager.get_web3_contract()

        self.logger = logging.getLogger(__name__)

        def handle_event(event):
            # Log the raw event data
            self.logger.info(f"Raw event data received: {event}")

            try:
                # Extract contract address and block number
                contract_addr = event.get('address', 'Unknown address')
                block_number = event.get('blockNumber', 'Unknown block')

                # Topic 0 contains the event signature hash, we don't need to decode this
                event_signature_hash = event['topics'][0].hex()

                # Topic 1 contains the indexed `contract_idx`
                contract_idx = int(event['topics'][1].hex(), 16)

                # The data field contains ABI-encoded `eventType` and `details`
                data = event['data']

                # Decode the data field
                decoded_data = decode(['string', 'string'], bytes(data))
                event_type = decoded_data[0]
                details = decoded_data[1]

                # Log decoded data for debugging
                self.logger.info(f"Decoded event: contract_idx={contract_idx}, event_type={event_type}, details={details}")

                # Store the event in the database
                Event.objects.create(
                    contract_idx=contract_idx,
                    contract_addr=contract_addr,
                    event_type=event_type,
                    details=details,
                    event_dt=block_number  # Block number as the event timestamp
                )
                self.logger.info(f'Successfully created ContractEvent for contract_idx={contract_idx}')

            except Exception as e:
                self.logger.error(f"Error handling event: {str(e)}")

        def create_event_filter():
            try:
                event_signature = "ContractEvent(uint256,string,string)"

                # Calculate the event topic by hashing the event signature
                event_topic = Web3.keccak(text=event_signature).hex()

                # Ensure the event topic has the 0x prefix
                if not event_topic.startswith("0x"):
                    event_topic = "0x" + event_topic

                # Create the filter with the contract address and the calculated event topic
                event_filter = self.w3.eth.filter({
                    'fromBlock': 'latest',
                    'address': self.w3_contract.address,
                    'topics': [event_topic]  # Use the hashed event signature as the topic
                })
                return event_filter
            except ValueError as e:
                self.logger.error(f'Error creating filter: {e}')
                self.stdout.write(self.style.ERROR(f'Error creating filter: {e}'))
                return None

        # Create the filter for events
        event_filter = create_event_filter()
        if event_filter is None:
            return

        self.logger.info('Started listening for contract events...')

        while True:
            try:
                # Get new entries from the event filter
                for event in event_filter.get_new_entries():
                    self.logger.info(f"Event found {event}")
                    handle_event(event)

                time.sleep(2)  # Pause to avoid excessive polling

            except ValueError as e:
                self.logger.error(f'Error getting new entries: {e}')
                self.stdout.write(self.style.ERROR(f'Error getting new entries: {e}'))
                if 'filter not found' in str(e):
                    self.logger.info('Recreating the event filter...')
                    event_filter = create_event_filter()
                    if event_filter is None:
                        return
            except Exception as e:
                self.logger.error(f'Unexpected error: {e}')
                self.stdout.write(self.style.ERROR(f'Unexpected error: {e}'))