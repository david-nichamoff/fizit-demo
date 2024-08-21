import time
from django.core.management.base import BaseCommand
from api.models.event_models import ContractEvent
import packages.load_web3 as load_web3

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Listen to contract events and store them in the database'

    def handle(self, *args, **kwargs):
        def handle_event(event):
            event_type = event['event']
            event_args = event['args']
            contract_addr = event.address

            logger.info(f'Handling event: {event_type} with args: {event_args}')

            if event_type == 'ContractEvent':
                ContractEvent.objects.create(
                    contract_idx=event_args['contract_idx'],
                    contract_addr = contract_addr,
                    event_type=event_args['eventType'],
                    details=event_args['details'],
                    event_dt=event['blockNumber']  
                )
                logger.info(f'Successfully created ContractEvent: {event_args}')
            else:
                logger.warning(f'Unknown event type: {event_type}')

        try:
            event_filter = w3_contract.events.ContractEvent.create_filter(fromBlock='latest')
        except ValueError as e:
            logger.error(f'Error creating filter: {e}')
            self.stdout.write(self.style.ERROR(f'Error creating filter: {e}'))
            return

        self.stdout.write(self.style.SUCCESS('Started listening for contract events...'))
        logger.info('Started listening for contract events...')

        while True:
            try:
                for event in event_filter.get_new_entries():
                    handle_event(event)

                time.sleep(2)

            except ValueError as e:
                logger.error(f'Error getting new entries: {e}')
                self.stdout.write(self.style.ERROR(f'Error getting new entries: {e}'))
            except Exception as e:
                logger.error(f'Unexpected error: {e}')
                self.stdout.write(self.style.ERROR(f'Unexpected error: {e}'))