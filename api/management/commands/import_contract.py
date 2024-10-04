import os
import json
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from api.managers import ConfigManager, SecretsManager
from api.interfaces import ContractAPI, PartyAPI, SettlementAPI, TransactionAPI, ArtifactAPI

class Command(BaseCommand):
    help = 'Import contract data from a file'

    def handle(self, *args, **kwargs):
        import_contract_addr = kwargs.get('contract_addr', False)

        if not import_contract_addr:
            self.stdout.write(self.style.ERROR('Contract address must be provided'))
            return

        # Initialize Config and Headers
        self._initialize_config()

        # Import the exported data if transfer_data flag is set
        fixture_file_path = os.path.join(settings.BASE_DIR, 'api', 'management', 'commands', 'fixtures', f'{import_contract_addr}_export.json')
        if os.path.exists(fixture_file_path):
            self._import_contract_data(fixture_file_path, import_contract_addr)
        else:
            self.stdout.write(self.style.ERROR(f'Fixture file not found: {fixture_file_path}'))

    def add_arguments(self, parser):
        parser.add_argument('--contract_addr', type=str, required=True, help="Contract addres of source data")

    def _initialize_config(self):
        # Initialize SecretsManager and ConfigManager to load keys and config
        self.secrets_manager = SecretsManager()
        self.config_manager = ConfigManager()

        # Load the keys and config from the respective managers
        self.keys = self.secrets_manager.load_keys()
        self.config = self.config_manager.load_config()

        # Set the headers for making requests, including authorization and content type
        self.headers = {
            'Authorization': f'Api-Key {self.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }

    def _import_contract_data(self, fixture_file_path, new_contract_address):
        with open(fixture_file_path, 'r') as fixture_file:
            data = json.load(fixture_file)

        for contract_key, contract_data in data.items():
            contract_idx = contract_data['contract_idx']
            self.stdout.write(self.style.SUCCESS(f'Importing data for contract_idx: {contract_idx}'))

            # Import contract
            self._import_contract(contract_data)

            # Import parties
            if contract_data.get('parties'):
                parties = contract_data.get('parties')
                self.stdout.write(self.style.SUCCESS(f'Importing parties for contract_idx: {contract_idx}'))
                self._import_parties(contract_idx, parties)

            # Import settlements
            if contract_data.get('settlements'):
                settlements = contract_data.get('settlements')
                self.stdout.write(self.style.SUCCESS(f'Importing settlements for contract_idx: {contract_idx}'))
                self._import_settlements(contract_idx, settlements)

            # Import transactions
            if contract_data.get('transactions'):
                transactions = contract_data.get('transactions')
                self.stdout.write(self.style.SUCCESS(f'Importing transactions for contract_idx: {contract_idx}'))
                self._import_transactions(contract_idx, transactions)

            # Import artifacts
            if contract_data.get('artifacts'):
                artifacts = contract_data.get('artifacts')
                self.stdout.write(self.style.SUCCESS(f'Importing artifacts for contract_idx: {contract_idx}'))
                self._import_artifacts(contract_idx, artifacts)

    def _import_contract(self, contract_data):
        contract_api = ContractAPI()
        try:
            contract_idx = contract_api.import_contract(contract_data)
            if contract_idx is not None:
                self.stdout.write(self.style.SUCCESS(f'Successfully imported contract {contract_data["contract_idx"]}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to import contract {contract_data["contract_idx"]}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing contract {contract_data["contract_idx"]}: {str(e)}'))
            logging.error(f'Error importing contract {contract_data["contract_idx"]}: {str(e)}')

    def _import_parties(self, contract_idx, party_data):
        party_api = PartyAPI()
        try:
            response = party_api.import_parties(contract_idx, party_data)
            if response:
                self.stdout.write(self.style.SUCCESS(f'Successfully imported parties for contract_idx: {contract_idx}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to import parties for contract_idx: {contract_idx}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing parties for contract_idx {contract_idx}: {str(e)}'))
            logging.error(f'Error importing parties for contract_idx {contract_idx}: {str(e)}')

    def _import_settlements(self, contract_idx, settlement_data):
        settlement_api = SettlementAPI()
        try:
            response = settlement_api.import_settlements(contract_idx, settlement_data)
            if response:
                self.stdout.write(self.style.SUCCESS(f'Successfully imported settlements for contract_idx: {contract_idx}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to import settlements for contract_idx: {contract_idx}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing settlements for contract_idx {contract_idx}: {str(e)}'))
            logging.error(f'Error importing settlements for contract_idx {contract_idx}: {str(e)}')

    def _import_transactions(self, contract_idx, transaction_data):
        transaction_api = TransactionAPI()
        try:
            response = transaction_api.import_transactions(contract_idx, transaction_data)
            if response:
                self.stdout.write(self.style.SUCCESS(f'Successfully imported transactions for contract_idx: {contract_idx}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to import transactions for contract_idx: {contract_idx}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing transactions for contract_idx {contract_idx}: {str(e)}'))
            logging.error(f'Error importing transactions for contract_idx {contract_idx}: {str(e)}')

    def _import_artifacts(self, contract_idx, artifact_data):
        artifact_api = ArtifactAPI()
        try:
            response = artifact_api.import_artifacts(contract_idx, artifact_data)
            if response:
                self.stdout.write(self.style.SUCCESS(f'Successfully imported artifacts for contract_idx: {contract_idx}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to import artifacts for contract_idx: {contract_idx}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing artifacts for contract_idx {contract_idx}: {str(e)}'))
            logging.error(f'Error importing artifacts for contract_idx {contract_idx}: {str(e)}')