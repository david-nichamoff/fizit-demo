import os
import json
from django.core.management.base import BaseCommand
from api.managers import SecretsManager, ConfigManager
from api.operations import ContractOperations


class Command(BaseCommand):
    help = 'Patch an existing contract using data from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--contract_idx', 
            type=str, 
            required=True, 
            help='The index of the contract to be patched'
        )

    def handle(self, *args, **options):
        # Initialize config and secrets
        self._initialize_config()

        # Get contract index
        contract_idx = options['contract_idx']

        # Load JSON file
        json_file_path = os.path.join(
            'api', 'management', 'commands', 'fixtures', 'contract', 'patch_contract.json'
        )
        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f'JSON file not found: {json_file_path}'))
            return

        with open(json_file_path, 'r') as file:
            patch_data = json.load(file)

        # Patch Contract Data
        self._patch_contract_data(contract_idx, patch_data)

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

    def _patch_contract_data(self, contract_idx, patch_data):
        response = self.contract_ops.patch_contract(contract_idx, patch_data)
        if response.status_code == 200:
            self.stdout.write(self.style.SUCCESS(f'Successfully patched contract: {contract_idx}'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to patch contract. Status: {response.status_code}, Response: {response.text}'))