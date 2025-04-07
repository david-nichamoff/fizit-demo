import logging
import requests

from django.core.management.base import BaseCommand

from api.utilities.bootstrap import build_app_context
from api.utilities.logging import  log_error, log_info, log_warning

class Command(BaseCommand):
    help = 'Retrieve and display formatted contract details, settlements, parties, transactions, and artifacts for a specific contract_idx'

    def add_arguments(self, parser):
        # Add contract_idx as an argument with the flag --contract_idx
        parser.add_argument('--contract_idx', type=int, required=True, help='The index of the contract to retrieve')
        parser.add_argument('--contract_type', type=str, required=True, help='The contract type to retrieve')

    def handle(self, *args, **kwargs):
        contract_idx = kwargs['contract_idx']
        contract_type = kwargs['contract_type']

        self.context = build_app_context()
        self.logger = logging.getLogger(__name__)

        self.headers = {
            'Authorization': f'Api-Key {self.context.secrets_manager.get_master_key()}',
            'Content-Type': 'application/json'
        }

        try:
            log_info(self.logger, f"Fetching formatted data for {contract_type}:{contract_idx}")
            contract_data = self.get_contract(contract_type, contract_idx)
            log_info(self.logger, f"Contract: {contract_data}")

            if self.context.api_manager.get_settlement_api(contract_type):
                settlements = self.get_settlements(contract_type, contract_idx)
                log_info(self.logger, f"Settlements: {settlements}")

            parties = self.get_parties(contract_type, contract_idx)
            log_info(self.logger, f"Parties: {parties}")
            transactions = self.get_transactions(contract_type, contract_idx)
            log_info(self.logger, f"Transactions: {transactions}")
            artifacts = self.get_artifacts(contract_type, contract_idx)
            log_info(self.logger, f"Artifacts: {artifacts}")

            # Print the data
            self.display_contract_data(contract_data)

            if self.context.api_manager.get_settlement_api(contract_type):
                self.display_settlements(settlements)

            self.display_parties(parties)
            self.display_transactions(transactions)
            self.display_artifacts(artifacts)

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error retrieving data: {str(e)}"))
            log_error(self.logger, f"Error retrieving data for {contract_type}:{contract_idx}: {str(e)}")

    def get_contract(self, contract_type, contract_idx):
        """Retrieve formatted contract data from the API."""
        response = requests.get(
            f"{self.context.config_manager.get_base_url()}/api/contracts/{contract_type}/{contract_idx}/",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_settlements(self, contract_type, contract_idx):
        """Retrieve formatted settlements data from the API."""
        response = requests.get(
            f"{self.context.config_manager.get_base_url()}/api/contracts/{contract_type}/{contract_idx}/settlements/",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_parties(self, contract_type, contract_idx):
        """Retrieve formatted parties data from the API."""
        response = requests.get(
            f"{self.context.config_manager.get_base_url()}/api/contracts/{contract_type}/{contract_idx}/parties/",

            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_transactions(self, contract_type, contract_idx):
        """Retrieve formatted transactions data from the API."""
        response = requests.get(
            f"{self.context.config_manager.get_base_url()}/api/contracts/{contract_type}/{contract_idx}/transactions/",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_artifacts(self, contract_type, contract_idx):
        """Retrieve formatted artifacts data from the API."""
        response = requests.get(
            f"{self.context.config_manager.get_base_url()}/api/contracts/{contract_type}/{contract_idx}/artifacts/",
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