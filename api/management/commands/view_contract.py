import logging
import requests

from django.core.management.base import BaseCommand
from api.managers import ConfigManager, SecretsManager

from api.utilities.logging import  log_error, log_info, log_warning

class Command(BaseCommand):
    help = 'Retrieve and display formatted contract details, settlements, parties, transactions, and artifacts for a specific contract_idx'

    def add_arguments(self, parser):
        # Add contract_idx as an argument with the flag --contract_idx
        parser.add_argument('--contract_idx', type=int, required=True, help='The index of the contract to retrieve')

    def handle(self, *args, **kwargs):
        contract_idx = kwargs['contract_idx']
        self.logger = logging.getLogger(__name__)

        # Initialize managers and headers
        self._initialize()

        try:
            log_info(self.logger, f"Fetching formatted data for contract {contract_idx}")
            contract_data = self.get_contract(contract_idx)
            settlements = self.get_settlements(contract_idx)
            parties = self.get_parties(contract_idx)
            transactions = self.get_transactions(contract_idx)
            artifacts = self.get_artifacts(contract_idx)

            # Print the data
            self.display_contract_data(contract_data)
            self.display_settlements(settlements)
            self.display_parties(parties)
            self.display_transactions(transactions)
            self.display_artifacts(artifacts)

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error retrieving data: {str(e)}"))
            log_error(self.logger, f"Error retrieving data for contract {contract_idx}: {str(e)}")

    def _initialize(self):
        """Initialize ConfigManager, SecretsManager, and request headers."""
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.secrets_manager = SecretsManager()
        self.keys = self.secrets_manager.load_keys()

        # Prepare headers with the correct format
        self.headers = {
            'Authorization': f'Api-Key {self.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }

    def get_contract(self, contract_idx):
        """Retrieve formatted contract data from the API."""
        response = requests.get(
            f"{self.config['url']}/api/contracts/{contract_idx}/",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_settlements(self, contract_idx):
        """Retrieve formatted settlements data from the API."""
        response = requests.get(
            f"{self.config['url']}/api/contracts/{contract_idx}/settlements/",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_parties(self, contract_idx):
        """Retrieve formatted parties data from the API."""
        response = requests.get(
            f"{self.config['url']}/api/contracts/{contract_idx}/parties/",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_transactions(self, contract_idx):
        """Retrieve formatted transactions data from the API."""
        response = requests.get(
            f"{self.config['url']}/api/contracts/{contract_idx}/transactions/",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_artifacts(self, contract_idx):
        """Retrieve formatted artifacts data from the API."""
        response = requests.get(
            f"{self.config['url']}/api/contracts/{contract_idx}/artifacts/",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def display_contract_data(self, contract_data):
        """Display formatted contract data in an easy-to-read format."""
        self.stdout.write(self.style.SUCCESS("\n--- Contract Data ---"))
        for key, value in contract_data.items():
            self.stdout.write(f"{key}: {value}")

    def display_settlements(self, settlements):
        """Display formatted settlements in an easy-to-read format."""
        self.stdout.write(self.style.SUCCESS("\n--- Settlements ---"))
        for idx, settlement in enumerate(settlements):
            self.stdout.write(self.style.SUCCESS(f"Settlement {idx + 1}:"))
            for key, value in settlement.items():
                self.stdout.write(f"{key}: {value}")

    def display_parties(self, parties):
        """Display formatted parties in an easy-to-read format."""
        self.stdout.write(self.style.SUCCESS("\n--- Parties ---"))
        for idx, party in enumerate(parties):
            self.stdout.write(self.style.SUCCESS(f"Party {idx + 1}:"))
            for key, value in party.items():
                self.stdout.write(f"{key}: {value}")

    def display_transactions(self, transactions):
        """Display formatted transactions in an easy-to-read format."""
        self.stdout.write(self.style.SUCCESS("\n--- Transactions ---"))
        for idx, transaction in enumerate(transactions):
            self.stdout.write(self.style.SUCCESS(f"Transaction {idx + 1}:"))
            for key, value in transaction.items():
                self.stdout.write(f"{key}: {value}")

    def display_artifacts(self, artifacts):
        """Display formatted artifacts in an easy-to-read format."""
        self.stdout.write(self.style.SUCCESS("\n--- Artifacts ---"))
        for idx, artifact in enumerate(artifacts):
            self.stdout.write(self.style.SUCCESS(f"Artifact {idx + 1}:"))
            for key, value in artifact.items():
                self.stdout.write(f"{key}: {value}")