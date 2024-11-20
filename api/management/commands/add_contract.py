import os
import json
from django.core.management.base import BaseCommand
from api.managers import SecretsManager, ConfigManager
from api.operations import ContractOperations

class Command(BaseCommand):
    help = 'Add a contract from a JSON file'

    def handle(self, *args, **kwargs):
        # Initialize config and secrets
        self._initialize_config()

        # Load JSON file
        json_file_path = os.path.join(
            'api', 'management', 'commands', 'fixtures', 'contract', 'contract.json'
        )
        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f'JSON file not found: {json_file_path}'))
            return

        with open(json_file_path, 'r') as file:
            contract_data = json.load(file)

        # Load Contract Data
        self._load_contract_data(contract_data)

    def _initialize_config(self):
        self.secrets_manager = SecretsManager()
        self.config_manager = ConfigManager()
        self.keys = self.secrets_manager.load_keys()
        self.config = self.config_manager.load_config()
        self.headers = {
            'Authorization': f'Api-Key {self.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }
        self.contract_ops = ContractOperations(self.headers, self.config)

    def _load_contract_data(self, data):
        response = self.contract_ops.load_contract(data)
        if response.status_code == 201:
            contract_idx = response.json()
            self.stdout.write(self.style.SUCCESS(f'Successfully added contract: {contract_idx}'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to add contract. Status: {response.status_code}'))