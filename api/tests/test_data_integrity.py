import os
import json

from datetime import datetime
from decimal import Decimal, ROUND_DOWN

from django.test import TestCase
from rest_framework import status

from .contract_operations import ContractOperations
from .party_operations import PartyOperations
from .settlement_operations import SettlementOperations
from .transaction_operations import TransactionOperations
from .utils import Utils
from .validate_events import validate_events

import packages.load_keys as load_keys
import packages.load_config as load_config

keys = load_keys.load_keys()
config = load_config.load_config()

class IntegrityTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        self.current_date = datetime.now().replace(microsecond=0).isoformat()
        self.headers = {
            'Authorization': f'Api-Key {keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }
        self.contract_ops = ContractOperations(self.headers, config)
        self.party_ops = PartyOperations(self.headers, config)
        self.settlement_ops = SettlementOperations(self.headers, config)
        self.transaction_ops = TransactionOperations(self.headers, config)
        self.utils = Utils(self.headers, config)

    def test_contract_integrity(self):
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_data_integrity', 'contract_errors')
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
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_data_integrity', 'party_errors')
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
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_data_integrity', 'settlement_errors')
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
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_data_integrity', 'transaction_errors')
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