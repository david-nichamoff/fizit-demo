import os
import json
from django.core.management.base import BaseCommand
from api.managers import SecretsManager, ConfigManager
from api.operations import SettlementOperations

class Command(BaseCommand):
    help = 'Add settlements to a specific contract from a JSON file'

    def add_arguments(self, parser):
        # Add a required argument for contract_idx
        parser.add_argument('--contract_idx', type=str, required=True, help="Contract index to associate settlements with")

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
            'api', 'management', 'commands', 'fixtures', 'contract', 'add_settlements.json'
        )
        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f'Settlements JSON file not found: {json_file_path}'))
            return

        with open(json_file_path, 'r') as file:
            settlements_data = json.load(file)

        # Load Settlements Data
        self._load_settlements(contract_idx, settlements_data)

    def _initialize_config(self):
        self.secrets_manager = SecretsManager()
        self.config_manager = ConfigManager()
        self.keys = self.secrets_manager.load_keys()
        self.config = self.config_manager.load_config()
        self.headers = {
            'Authorization': f'Api-Key {self.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }
        self.settlement_ops = SettlementOperations(self.headers, self.config)

    def _load_settlements(self, contract_idx, settlements_data):
        # Use SettlementOperations to post settlements
        response = self.settlement_ops.post_settlements(contract_idx, settlements_data)
        if response.status_code == 201:
            self.stdout.write(self.style.SUCCESS(f'Successfully added settlements to contract {contract_idx}'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to add settlements. Status: {response.status_code}'))