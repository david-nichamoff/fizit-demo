import os
import logging
import json
from django.core.management.base import BaseCommand
from api.managers import SecretsManager, ConfigManager
from api.operations import BankOperations, CsrfOperations


class Command(BaseCommand):
    help = 'Fetches and optionally posts deposits for a specified contract_idx'

    def add_arguments(self, parser):
        # Add contract_idx as an argument with the flag --contract_idx
        parser.add_argument('--contract_idx', type=int, required=True, help='The index of the contract to retrieve and post deposits for')
        # Add --post as an optional argument
        parser.add_argument('--post', action='store_true', help='If set, posts the deposits back to the API')

    def handle(self, *args, **kwargs):
        contract_idx = kwargs['contract_idx']
        post_deposits = kwargs['post']  # Retrieve the value of --post
        self.logger = logging.getLogger(__name__)

        # Initialize config and secrets
        self._initialize_config()

        try:
            # Load the start_date and end_date from the JSON file
            date_range = self._load_date_range()
            if not date_range:
                return  # Exit if the file is not found
            start_date = date_range['start_date']
            end_date = date_range['end_date']

            # Fetch and print deposits
            deposits = self.get_deposits(contract_idx, start_date, end_date)
            self.stdout.write(self.style.SUCCESS("\n--- Deposits ---"))
            for deposit in deposits:
                self.stdout.write(f"{deposit}")

            # Conditionally post deposits if --post is set
            if post_deposits:
                self.logger.info(f"Posting deposits for contract {contract_idx}")
                self.post_deposits(contract_idx, deposits)

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error processing deposits for contract {contract_idx}: {str(e)}"))
            self.logger.error(f"Error processing deposits for contract {contract_idx}: {str(e)}")

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

        # Initialize BankOperations and CsrfOperations
        self.bank_ops = BankOperations(self.headers, self.config)
        self.csrf_ops = CsrfOperations(self.headers, self.config)

    def _load_date_range(self):
        """Load the start_date and end_date from add_deposits.json."""
        # Use the specified pattern to locate the JSON file
        json_file_path = os.path.join(
            'api', 'management', 'commands', 'fixtures', 'contract', 'add_deposits.json'
        )
        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f'JSON file not found: {json_file_path}'))
            return None

        with open(json_file_path, 'r') as f:
            return json.load(f)

    def get_deposits(self, contract_idx, start_date, end_date):
        """Retrieve deposits for a specific contract."""

        response = self.bank_ops.get_deposits(contract_idx, start_date, end_date)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to retrieve deposits. Status: {response.status_code}\nResponse: {response.text}")

    def post_deposits(self, contract_idx, deposits):
        """Post deposits to a specific contract."""
        csrf_token = self.csrf_ops._get_csrf_token()
        response = self.bank_ops.add_deposits(contract_idx, deposits, csrf_token)
        if response.status_code == 201:
            self.stdout.write(self.style.SUCCESS(f"Successfully added deposits for contract {contract_idx}"))
        else:
            raise Exception(f"Failed to add deposits. Status: {response.status_code}\nResponse: {response.text}")