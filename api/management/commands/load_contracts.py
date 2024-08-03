import os
import json
import requests

from django.core.management.base import BaseCommand

import packages.load_keys as load_keys
import packages.load_config as load_config
import packages.load_abi as load_abi

class Command(BaseCommand):

    keys = load_keys.load_keys()
    config = load_config.load_config()
    abi = load_abi.load_abi()

    help = 'Load contracts and parties from JSON files'

    headers = {
        'Authorization': f'Api-Key {keys["FIZIT_MASTER_KEY"]}',
        'Content-Type': 'application/json'
    }

    def handle(self, *args, **kwargs):
        fixtures_dir = os.path.join(os.path.dirname(__file__), '../../fixtures/contracts/')
        for filename in os.listdir(fixtures_dir):
            if filename.endswith('.json'):
                with open(os.path.join(fixtures_dir, filename), 'r') as file:
                    try:
                        data = json.load(file)
                        self._load_contract(data['contract'], data['parties'])
                    except json.JSONDecodeError as e:
                        self.stdout.write(self.style.ERROR(f'Error decoding JSON from file: {filename}, Error: {str(e)}'))
                    except KeyError as e:
                        self.stdout.write(self.style.ERROR(f'Missing key in JSON from file: {filename}, Error: {str(e)}'))

    def _load_contract(self, contract_data, parties_data):
        response = requests.post(
            f"{self.config['url']}/api/contracts/",
            json=contract_data,
            headers=self.headers
        )

        if response.status_code == 201:
            try:
                contract_idx = response.json()
                self.stdout.write(self.style.SUCCESS(f'Successfully added contract "{contract_data['contract_name']}"'))
                self._add_parties(contract_idx, parties_data)
            except json.JSONDecodeError:
                self.stdout.write(self.style.ERROR('Failed to parse JSON response from the server'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to add contract "{contract_data['contract_name']}". Status code: {response.status_code}'))
            self.stdout.write(self.style.ERROR(f'Headers: {self.headers}'))
            self.stdout.write(self.style.ERROR(f'Payload: {json.dumps(contract_data)}'))
            self.stdout.write(self.style.ERROR(f'Response: {response.text}'))

    def _add_parties(self, contract_idx, parties_data):
        response = requests.post(
            f"{self.config['url']}/api/contracts/{contract_idx}/parties/",
            json=parties_data,
            headers=self.headers
        )

        if response.status_code == 201:
            self.stdout.write(self.style.SUCCESS(f'Successfully added parties to contract {contract_idx}'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to add parties to contract {contract_idx}. Status code: {response.status_code}'))
            self.stdout.write(self.style.ERROR(f'Headers: {self.headers}'))
            self.stdout.write(self.style.ERROR(f'Payload: {json.dumps(parties_data)}'))
            self.stdout.write(self.style.ERROR(f'Response: {response.text}'))