import os
import json
from datetime import datetime

from django.test import TestCase
from rest_framework import status

from api.operations import ContractOperations, PartyOperations, SettlementOperations
from api.operations import TransactionOperations, ArtifactOperations, CsrfOperations

from api.managers import SecretsManager, ConfigManager

class ContractTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        self.secrets_manager = SecretsManager()
        self.config_manager = ConfigManager()

        self.keys = self.secrets_manager.load_keys()
        self.config = self.config_manager.load_config()

        self.current_date = datetime.now().replace(microsecond=0).isoformat()
        self.headers = {
            'Authorization': f'Api-Key {self.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }

        self.contract_ops = ContractOperations(self.headers, self.config)
        self.party_ops = PartyOperations(self.headers, self.config)
        self.settlement_ops = SettlementOperations(self.headers, self.config)
        self.transaction_ops = TransactionOperations(self.headers, self.config)
        self.artifact_ops = ArtifactOperations(self.headers, self.config)
        self.csrf_ops = CsrfOperations(self.headers, self.config)

    def test_load_contract(self):
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_full_contract')
        for filename in os.listdir(fixtures_dir):
            if filename.endswith('.json'):
                with open(os.path.join(fixtures_dir, filename), 'r') as file:
                    try:
                        data = json.load(file)
                        print(f"Loading contract from file: {filename}")
                        self._load_contract_data(data)
                    except json.JSONDecodeError as e:
                        self.fail(f'Error decoding JSON from file: {filename}, Error: {str(e)}')
                    except KeyError as e:
                        self.fail(f'Missing key in JSON from file: {filename}, Error: {str(e)}')

    def _load_contract_data(self, data):
        # Load the contract
        response = self.contract_ops.load_contract(data['contract'])
        if response.status_code == status.HTTP_201_CREATED:
            contract_idx = response.json()
            print(f'Successfully added contract: {contract_idx}')

            # Load the parties
            if 'parties' in data:
                self._load_parties(contract_idx, data['parties'])

            # Load the settlements
            if 'settlements' in data:
                self._load_settlements(contract_idx, data['settlements'])

            # Load the transactions
            if 'transactions' in data:
                self._load_transactions(contract_idx, data['transactions'])

            # Load the artifacts
            if 'artifacts' in data:
                self._load_artifacts(contract_idx, data['artifacts'])

        else:
            self.fail(f'Failed to add contract. Status code: {response.status_code}\nResponse: {response.text}')

    def _load_parties(self, contract_idx, parties_data):
        response = self.party_ops.add_parties(contract_idx, parties_data)
        if response.status_code == status.HTTP_201_CREATED:
            print(f'Successfully added parties to contract {contract_idx}')
        else:
            self.fail(f'Failed to add parties to contract {contract_idx}. Status code: {response.status_code}\nResponse: {response.text}')

    def _load_settlements(self, contract_idx, settlements_data):
        response = self.settlement_ops.post_settlements(contract_idx, settlements_data)
        if response.status_code == status.HTTP_201_CREATED:
            print(f'Successfully added settlements to contract {contract_idx}')
        else:
            self.fail(f'Failed to add settlements to contract {contract_idx}. Status code: {response.status_code}\nResponse: {response.text}')

    def _load_transactions(self, contract_idx, transactions_data):
        response = self.transaction_ops.post_transactions(contract_idx, transactions_data)
        if response.status_code == status.HTTP_201_CREATED:
            print(f'Successfully added transactions to contract {contract_idx}')
        else:
            self.fail(f'Failed to add transactions to contract {contract_idx}. Status code: {response.status_code}\nResponse: {response.text}')

    def _load_artifacts(self, contract_idx, artifact_urls):
        csrf_token = self.csrf_ops._get_csrf_token()
        response = self.artifact_ops.add_artifacts(contract_idx, artifact_urls, csrf_token)
        if response.status_code == status.HTTP_201_CREATED:
            print(f'Successfully added artifacts to contract {contract_idx}')
        else:
            self.fail(f'Failed to add artifacts to contract {contract_idx}. Status code: {response.status_code}\nResponse: {response.text}')