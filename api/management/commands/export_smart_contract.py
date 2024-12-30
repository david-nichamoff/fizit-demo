import os
import json
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from api.managers import ConfigManager, SecretsManager

class Command(BaseCommand):
    help = 'Export smart contract'

    def handle(self, *args, **kwargs):

        # Initialize Config and Headers
        self._initialize_config()
        self._export_contract_data()

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

    def _export_contract_data(self):
        data = {}

        # Get the count of contracts
        count_response = requests.get(f"{self.config['url']}/api/contracts/count/", headers=self.headers)
        if count_response.status_code != 200:
            self.stdout.write(self.style.ERROR('Failed to retrieve contract count'))
            return
        
        contract_count = count_response.json()['contract_count']

        # Loop through contracts and export data
        for contract_idx in range(contract_count):
            self.stdout.write(self.style.SUCCESS(f'Exporting data for contract_idx: {contract_idx}'))

            # Get contract data
            contract_response = requests.get(f"{self.config['url']}/api/contracts/{contract_idx}/", headers=self.headers)
            if contract_response.status_code == 200:
                data[f'contract_{contract_idx}'] = contract_response.json()
            else:
                self.stdout.write(self.style.ERROR(f"Failed to retrieve contract data for contract_idx {contract_idx}"))
                continue

            # Get party data
            party_response = requests.get(f"{self.config['url']}/api/contracts/{contract_idx}/parties/", headers=self.headers)
            if party_response.status_code == 200:
                data[f'contract_{contract_idx}']['parties'] = party_response.json()
            else:
                self.stdout.write(self.style.ERROR(f"Failed to retrieve parties for contract_idx {contract_idx}"))

            # Get settlement data
            settlement_response = requests.get(f"{self.config['url']}/api/contracts/{contract_idx}/settlements/", headers=self.headers)
            if settlement_response.status_code == 200:
                data[f'contract_{contract_idx}']['settlements'] = settlement_response.json()
            else:
                self.stdout.write(self.style.ERROR(f"Failed to retrieve settlements for contract_idx {contract_idx}"))

            # Get transaction data
            transaction_response = requests.get(f"{self.config['url']}/api/contracts/{contract_idx}/transactions/", headers=self.headers)
            if transaction_response.status_code == 200:
                data[f'contract_{contract_idx}']['transactions'] = transaction_response.json()
            else:
                self.stdout.write(self.style.ERROR(f"Failed to retrieve transactions for contract_idx {contract_idx}"))

            # Get artifact data
            artifact_response = requests.get(f"{self.config['url']}/api/contracts/{contract_idx}/artifacts/", headers=self.headers)
            if artifact_response.status_code == 200:
                data[f'contract_{contract_idx}']['artifacts'] = artifact_response.json()
            else:
                self.stdout.write(self.style.ERROR(f"Failed to retrieve artifacts for contract_idx {contract_idx}"))

        # Save the exported data to a JSON file
        export_file_path = os.path.join(settings.BASE_DIR, 'api', 'management', 'commands', 'fixtures', 'export', f'{self.config['contract_addr']}_export.json')

        os.makedirs(os.path.dirname(export_file_path), exist_ok=True)
        with open(export_file_path, 'w') as f:
            json.dump(data, f, indent=4)
        self.stdout.write(self.style.SUCCESS(f'Exported contract data to {export_file_path}'))