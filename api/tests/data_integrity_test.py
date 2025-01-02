import os
import json
from datetime import datetime

from django.test import TestCase
from rest_framework import status

from api.operations import ContractOperations, PartyOperations, SettlementOperations
from api.operations import TransactionOperations, CsrfOperations

from api.managers import SecretsManager, ConfigManager

class IntegrityTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Initialize SecretsManager and ConfigManager as singletons
        cls.secrets_manager = SecretsManager()
        cls.config_manager = ConfigManager()

        # Load keys and config once and store them in class variables
        cls.keys = cls.secrets_manager.load_keys()
        cls.config = cls.config_manager.load_config()

    def setUp(self):
        self.current_date = datetime.now().replace(microsecond=0).isoformat()
        self.headers = {
            'Authorization': f'Api-Key {self.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }
        self.contract_ops = ContractOperations(self.headers, self.config)
        self.party_ops = PartyOperations(self.headers, self.config)
        self.settlement_ops = SettlementOperations(self.headers, self.config)
        self.transaction_ops = TransactionOperations(self.headers, self.config)
        self.csrf_ops = CsrfOperations(self.headers, self.config)

    def test_contract_integrity(self):
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'data_integrity_test', 'contract_errors')
        for filename in os.listdir(fixtures_dir):
            if filename.endswith('.json'):
                with open(os.path.join(fixtures_dir, filename), 'r') as file:
                    try:
                        data = json.load(file)
                        print(f"Loading contract from file: {filename}")
                        self._run_contract_integrity(data['contract'])
                    except json.JSONDecodeError as e:
                        self.fail(f'Error decoding JSON from file: {filename}, Error: {str(e)}')
                    except KeyError as e:
                        self.fail(f'Missing key in JSON from file: {filename}, Error: {str(e)}')

    def _run_contract_integrity(self, contract_data):
        response = self.contract_ops.load_contract(contract_data)
        if response.status_code != status.HTTP_400_BAD_REQUEST:
            self.fail(f"Expected a 400 Bad Request status for an invalid contract type, "
                f"but got {response.status_code}.\nResponse: {response.text}")

    def test_party_integrity(self):
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'data_integrity_test', 'party_errors')
        for filename in os.listdir(fixtures_dir):
            if filename.endswith('.json'):
                with open(os.path.join(fixtures_dir, filename), 'r') as file:
                    try:
                        data = json.load(file)
                        print(f"Loading party data from file: {filename}")
                        response = self.contract_ops.load_contract(data["contract"])
                        contract_idx = response.text
                        self._run_party_integrity(contract_idx, data['parties'])
                    except json.JSONDecodeError as e:
                        self.fail(f'Error decoding JSON from file: {filename}, Error: {str(e)}')
                    except KeyError as e:
                        self.fail(f'Missing key in JSON from file: {filename}, Error: {str(e)}')

    def _run_party_integrity(self, contract_idx, parties_data):
        response = self.party_ops.add_parties(contract_idx, parties_data)
        if response.status_code != status.HTTP_400_BAD_REQUEST:
            self.fail(f"Expected a 400 Bad Request status for invalid party data, "
                      f"but got {response.status_code}.\nResponse: {response.text}")

    def test_settlement_integrity(self):
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'data_integrity_test', 'settlement_errors')
        for filename in os.listdir(fixtures_dir):
            if filename.endswith('.json'):
                with open(os.path.join(fixtures_dir, filename), 'r') as file:
                    try:
                        data = json.load(file)
                        print(f"Loading settlement data from file: {filename}")
                        response = self.contract_ops.load_contract(data["contract"])
                        contract_idx = response.text
                        self._run_settlement_integrity(contract_idx, data['settlements'])
                    except json.JSONDecodeError as e:
                        self.fail(f'Error decoding JSON from file: {filename}, Error: {str(e)}')
                    except KeyError as e:
                        self.fail(f'Missing key in JSON from file: {filename}, Error: {str(e)}')

    def _run_settlement_integrity(self, contract_idx, settlements_data):
        response = self.settlement_ops.post_settlements(contract_idx, settlements_data)
        if response.status_code != status.HTTP_400_BAD_REQUEST:
            self.fail(f"Expected a 400 Bad Request status for invalid settlement data, "
                      f"but got {response.status_code}.\nResponse: {response.text}")

    def test_transaction_integrity(self):
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'data_integrity_test', 'transaction_errors')
        for filename in os.listdir(fixtures_dir):
            if filename.endswith('.json'):
                with open(os.path.join(fixtures_dir, filename), 'r') as file:
                    try:
                        data = json.load(file)
                        print(f"Loading transaction data from file: {filename}")
                        response = self.contract_ops.load_contract(data["contract"])
                        contract_idx = response.text
                        self._run_transaction_integrity(contract_idx, data['transactions'])
                    except json.JSONDecodeError as e:
                        self.fail(f'Error decoding JSON from file: {filename}, Error: {str(e)}')
                    except KeyError as e:
                        self.fail(f'Missing key in JSON from file: {filename}, Error: {str(e)}')

    def _run_transaction_integrity(self, contract_idx, transactions_data):
        response = self.transaction_ops.post_transactions(contract_idx, transactions_data)
        if response.status_code != status.HTTP_400_BAD_REQUEST:
            self.fail(f"Expected a 400 Bad Request status for invalid transaction data, "
                    f"but got {response.status_code}.\nResponse: {response.text}")