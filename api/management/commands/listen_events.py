import logging
import time

from django.core.management.base import BaseCommand
from api.models.event_models import Event
from api.managers import Web3Manager, ConfigManager

class Command(BaseCommand):
    help = 'Listen to contract events and store them in the database'

    def handle(self, *args, **kwargs):
        # Initialize components in the handle method
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.w3_manager = Web3Manager()
        self.w3 = self.w3_manager.get_web3_instance()
        self.w3_contract = self.w3_manager.get_web3_contract()

        self.logger = logging.getLogger(__name__)

        def handle_event(event):
            event_type = event['event']
            event_args = event['args']
            contract_addr = event.address

            self.logger.info(f'Handling event: {event_type} with args: {event_args}')

            if event_type == 'ContractEvent':
                Event.objects.create(
                    contract_idx=event_args['contract_idx'],
                    contract_addr=contract_addr,
                    event_type=event_args['eventType'],
                    details=event_args['details'],
                    event_dt=event['blockNumber']  
                )
                self.logger.info(f'Successfully created ContractEvent: {event_args}')
            else:
                self.logger.warning(f'Unknown event type: {event_type}')

        def create_event_filter():
            try:
                return self.w3_contract.events.ContractEvent.create_filter(fromBlock='latest')
            except ValueError as e:
                self.logger.error(f'Error creating filter: {e}')
                self.stdout.write(self.style.ERROR(f'Error creating filter: {e}'))
                return None

        event_filter = create_event_filter()
        if event_filter is None:
            return

        self.logger.info('Started listening for contract events...')

        while True:
            try:
                for event in event_filter.get_new_entries():
                    handle_event(event)

                time.sleep(2)

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