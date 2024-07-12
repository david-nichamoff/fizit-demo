import time
from django.core.management.base import BaseCommand
from api.models import ContractEvent
import packages.web3_client
import packages.env_var

env_var = packages.env_var.get_env()
w3 = packages.web3_client.get_web3_instance()
w3_contract = packages.web3_client.get_web3_contract()

class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        def handle_event(event):
            event_type = event['event']
            event_args = event['args']

            if event_type == 'ContractEvent':
                ContractEvent.objects.create(
                    contract_idx=event_args['contract_idx'],
                    event_type=event_args['eventType'],
                    details=event_args['details']
                )
            else:
                self.stdout.write(self.style.WARNING(f'Unknown event type: {event_type}'))

        event_filter = w3_contract.events.ContractEvent.create_filter(fromBlock='latest')

        while True:
            for event in event_filter.get_new_entries():
                handle_event(event)
            time.sleep(10)