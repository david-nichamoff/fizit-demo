import os
import json
from django.core.management.base import BaseCommand
from api.managers import SecretsManager, ConfigManager
from api.operations import PartyOperations

class Command(BaseCommand):
    help = 'Add parties to a specific contract from a JSON file'

    def add_arguments(self, parser):
        # Add a required argument for contract_idx
        parser.add_argument('--contract_idx', type=str, required=True, help="Contract index to associate parties with")

    def handle(self, *args, **kwargs):
        # Get contract_idx from arguments
        contract_idx = kwargs.get('contract_idx')
        if not contract_idx:
            self.stdout.write(self.style.ERROR('Contract index (contract_idx) must be provided'))
            return

        # Initialize config and secrets
        self._initialize_config()

        # Load JSON file
        json_file_path = os.path.join(
            'api', 'management', 'commands', 'fixtures', 'contract', 'add_parties.json'
        )
        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f'Parties JSON file not found: {json_file_path}'))
            return

        with open(json_file_path, 'r') as file:
            parties_data = json.load(file)

        # Load Parties Data
        self._load_parties(contract_idx, parties_data)

    def _initialize_config(self):
        self.secrets_manager = SecretsManager()
        self.config_manager = ConfigManager()
        self.keys = self.secrets_manager.load_keys()
        self.config = self.config_manager.load_config()
        self.headers = {
            'Authorization': f'Api-Key {self.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }
        self.party_ops = PartyOperations(self.headers, self.config)

    def _load_parties(self, contract_idx, parties_data):
        # Use PartyOperations to add parties
        response = self.party_ops.add_parties(contract_idx, parties_data)
        if response.status_code == 201:
            self.stdout.write(self.style.SUCCESS(f'Successfully added parties to contract {contract_idx}'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to add parties. Status: {response.status_code}\nResponse: {response.text}'))