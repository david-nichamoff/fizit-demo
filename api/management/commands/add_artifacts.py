import os
import json
from django.core.management.base import BaseCommand
from api.managers import SecretsManager, ConfigManager
from api.operations import ArtifactOperations, CsrfOperations

class Command(BaseCommand):
    help = 'Add artifacts to a specific contract from a JSON file'

    def add_arguments(self, parser):
        # Add a required argument for contract_idx
        parser.add_argument('--contract_idx', type=str, required=True, help="Contract index to associate artifacts with")

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
            'api', 'management', 'commands', 'fixtures', 'contract', 'add_artifacts.json'
        )
        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f'Artifacts JSON file not found: {json_file_path}'))
            return

        with open(json_file_path, 'r') as file:
            artifacts_data = json.load(file)

        # Load Artifacts Data
        self._load_artifacts(contract_idx, artifacts_data)

    def _initialize_config(self):
        self.secrets_manager = SecretsManager()
        self.config_manager = ConfigManager()
        self.keys = self.secrets_manager.load_keys()
        self.config = self.config_manager.load_config()
        self.headers = {
            'Authorization': f'Api-Key {self.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }
        self.artifact_ops = ArtifactOperations(self.headers, self.config)
        self.csrf_ops = CsrfOperations(self.headers, self.config)

    def _load_artifacts(self, contract_idx, artifacts_data):
        # Get CSRF token if needed by ArtifactOperations
        csrf_token = self.csrf_ops._get_csrf_token()

        # Use ArtifactOperations to add artifacts
        response = self.artifact_ops.add_artifacts(contract_idx, artifacts_data, csrf_token)
        if response.status_code == 201:
            self.stdout.write(self.style.SUCCESS(f'Successfully added artifacts to contract {contract_idx}'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to add artifacts. Status: {response.status_code}\nResponse: {response.text}'))