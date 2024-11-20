import os
import json
import logging
from decimal import Decimal
from django.core.management.base import BaseCommand
from api.managers import SecretsManager, ConfigManager
from api.operations import BankOperations, CsrfOperations

class Command(BaseCommand):
    help = 'Retrieve and post matching deposits for a specific contract_idx'

    def add_arguments(self, parser):
        # Add contract_idx as an argument with the flag --contract_idx
        parser.add_argument('--contract_idx', type=int, required=True, help='The index of the contract to retrieve and post deposits for')

    def handle(self, *args, **kwargs):
        contract_idx = kwargs['contract_idx']
        self.logger = logging.getLogger(__name__)

        # Initialize config and secrets
        self._initialize_config()

        # Load JSON file
        json_file_path = os.path.join(
            'api', 'management', 'commands', 'fixtures', 'contract', 'deposits.json'
        )
        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f'Deposits JSON file not found: {json_file_path}'))
            return

        with open(json_file_path, 'r') as file:
            deposits_data = json.load(file)

        # Extract parameters and expected deposit details
        params = deposits_data['params']
        expected_deposit = deposits_data['deposits']

        try:
            # Retrieve and check for matching deposits
            self.logger.info(f"Fetching deposits for contract {contract_idx} within specified date range")
            matching_deposit = self.get_matching_deposit(contract_idx, params, expected_deposit)

            if matching_deposit:
                self.logger.info(f"Matching deposit found for contract {contract_idx}. Posting deposit to API.")
                self.post_deposit(contract_idx, matching_deposit)
            else:
                self.stdout.write(self.style.WARNING("No matching deposit found."))

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

    def get_matching_deposit(self, contract_idx, params, expected_deposit):
        """Retrieve deposits and find one that matches the expected deposit data."""
        start_date = params["start_date"]
        end_date = params["end_date"]

        # Use BankOperations to get deposits
        response = self.bank_ops.get_deposits(contract_idx, start_date, end_date)
        if response.status_code != 200:
            raise Exception(f"Failed to retrieve deposits. Status: {response.status_code}\nResponse: {response.text}")

        deposits = response.json()

        # Check if one of the deposits matches the expected result
        for deposit in deposits:
            if (deposit['bank'] == expected_deposit['bank'] and
                deposit['account_id'] == expected_deposit['account_id'] and
                deposit['deposit_id'] == expected_deposit['deposit_id'] and
                deposit['counterparty'] == expected_deposit['counterparty'] and
                Decimal(deposit['deposit_amt']) == Decimal(expected_deposit['deposit_amt']) and
                deposit['deposit_dt'] == expected_deposit['deposit_dt']):
                return expected_deposit  # Return the expected deposit if it matches

        return None  # No matching deposit found

    def post_deposit(self, contract_idx, deposit_data):
        """Post deposit to the API for a specific contract."""
        csrf_token = self.csrf_ops._get_csrf_token()
        response = self.bank_ops.add_deposits(contract_idx, [deposit_data], csrf_token)
        if response.status_code == 201:
            self.stdout.write(self.style.SUCCESS(f"Successfully added deposit for contract {contract_idx}"))
        else:
            raise Exception(f"Failed to add deposit. Status: {response.status_code}\nResponse: {response.text}")