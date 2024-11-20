import logging
from django.core.management.base import BaseCommand
from api.managers import SecretsManager, ConfigManager
from api.operations import BankOperations, CsrfOperations

class Command(BaseCommand):
    help = 'Fetches and optionally posts advances for a specified contract_idx'

    def add_arguments(self, parser):
        # Add contract_idx as an argument with the flag --contract_idx
        parser.add_argument('--contract_idx', type=int, required=True, help='The index of the contract to retrieve and post advances for')
        # Add --post as an optional argument
        parser.add_argument('--post', action='store_true', help='If set, posts the advances back to the API')

    def handle(self, *args, **kwargs):
        contract_idx = kwargs['contract_idx']
        post_advances = kwargs['post']  # Retrieve the value of --post
        self.logger = logging.getLogger(__name__)

        # Initialize config and secrets
        self._initialize_config()

        try:
            # Fetch and print advances
            self.logger.info(f"Fetching advances for contract {contract_idx}")
            advances = self.get_advances(contract_idx)
            print("\n--- Advances ---")
            for advance in advances:
                print(advance)

            # Conditionally post advances if --post is set
            if post_advances:
                self.logger.info(f"Posting advances for contract {contract_idx}")
                self.post_advances(contract_idx, advances)

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error processing advances for contract {contract_idx}: {str(e)}"))
            self.logger.error(f"Error processing advances for contract {contract_idx}: {str(e)}")

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

    def get_advances(self, contract_idx):
        """Retrieve advances for a specific contract."""
        response = self.bank_ops.get_advances(contract_idx)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to retrieve advances. Status: {response.status_code}\nResponse: {response.text}")

    def post_advances(self, contract_idx, advances):
        """Post advances to a specific contract."""
        csrf_token = self.csrf_ops._get_csrf_token()
        response = self.bank_ops.add_advances(contract_idx, advances, csrf_token)
        if response.status_code == 201:
            self.stdout.write(self.style.SUCCESS(f"Successfully added advances for contract {contract_idx}"))
        else:
            raise Exception(f"Failed to add advances. Status: {response.status_code}\nResponse: {response.text}")