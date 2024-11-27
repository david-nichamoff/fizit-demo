import os
import json
from django.core.management.base import BaseCommand
from api.managers import SecretsManager, ConfigManager
from api.operations import ContractOperations

class Command(BaseCommand):
    help = 'Add contracts from a JSON file'

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
            contracts_data = json.load(file)

        if not isinstance(contracts_data, list):
            self.stdout.write(self.style.ERROR(f'Invalid JSON format. Expected an array of contracts.'))
            return

        # Load all contracts in the array
        self._load_contracts(contracts_data)

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

    def _load_contracts(self, contracts_data):
        for index, contract_data in enumerate(contracts_data, start=1):
            self.stdout.write(f'Processing contract {index}/{len(contracts_data)}...')
            response = self.contract_ops.load_contract(contract_data)
            if response.status_code == 201:
                contract_idx = response.json()
                self.stdout.write(self.style.SUCCESS(f'Successfully added contract: {contract_idx}'))
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to add contract {index}. Status: {response.status_code}, Error: {response.text}')
                )