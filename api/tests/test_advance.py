import os
import json

from datetime import datetime

from django.test import TestCase
from rest_framework import status

import packages.load_keys as load_keys
import packages.load_config as load_config

from .bank_operations import BankOperations
from .contract_operations import ContractOperations
from .party_operations import PartyOperations
from .settlement_operations import SettlementOperations
from .transaction_operations import TransactionOperations

keys = load_keys.load_keys()
config = load_config.load_config()

class BankInterfaceTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        self.current_date = datetime.now().replace(microsecond=0).isoformat()
        self.headers = {
            'Authorization': f'Api-Key {keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }
        self.bank_ops = BankOperations(self.headers, config)
        self.contract_ops = ContractOperations(self.headers, config)
        self.party_ops = PartyOperations(self.headers, config)
        self.settlement_ops = SettlementOperations(self.headers, config)
        self.transaction_ops = TransactionOperations(self.headers, config)

    def test_bank_interface(self):
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_bank_interface')
        for filename in os.listdir(fixtures_dir):
            if filename.endswith('.json'):
                with open(os.path.join(fixtures_dir, filename), 'r') as file:
                    try:
                        data = json.load(file)
                        print(f"Loading contract data from file: {filename}")
                        contract_idx = self._test_create_contract(data['contract'])
                        self._test_load_parties(contract_idx, data['parties'])
                        self._test_load_settlements(contract_idx, data['settlements'])
                        self._test_load_transactions(contract_idx, data['transactions'])
                        self._test_account_endpoint(data['contract'])
                        self._test_recipient_endpoint(data['contract'])
                    except json.JSONDecodeError as e:
                        self.fail(f'Error decoding JSON from file: {filename}, Error: {str(e)}')
                    except KeyError as e:
                        self.fail(f'Missing key in JSON from file: {filename}, Error: {str(e)}')

    def _test_create_contract(self, contract_data):
        response = self.contract_ops.load_contract(contract_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Failed to create contract.")
        contract_idx = response.json()
        self.assertIsNotNone(contract_idx, 'Contract index should not be None')
        return contract_idx

    def _test_load_parties(self, contract_idx, parties_data):
        response = self.party_ops.add_parties(contract_idx, parties_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, f"Failed to add parties to contract {contract_idx}.")

    def _test_load_settlements(self, contract_idx, settlements_data):
        response = self.settlement_ops.post_settlements(contract_idx, settlements_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, f"Failed to add settlements to contract {contract_idx}.")

    def _test_load_transactions(self, contract_idx, transactions_data):
        response = self.transaction_ops.post_transactions(contract_idx, transactions_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, f"Failed to add transactions to contract {contract_idx}.")

    def _test_account_endpoint(self, contract_data):
        bank = contract_data['funding_instr']['bank']
        account_id = contract_data['funding_instr']['account_id']

        response = self.bank_ops.get_accounts(bank)
        
        # Check if the response is JSON
        if response.headers['Content-Type'] != 'application/json':
            self.fail(f"Expected JSON response but got {response.headers['Content-Type']}.\nResponse content: {response.content.decode('utf-8')}")

        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed to get accounts for bank {bank}.")
        
        accounts = response.json()
        account_ids = [account['account_id'] for account in accounts]
        self.assertIn(account_id, account_ids, f"Account ID {account_id} not found in response.")

    def _test_recipient_endpoint(self, contract_data):
        bank = contract_data['funding_instr']['bank']
        recipient_id = contract_data['funding_instr']['recipient_id']

        response = self.bank_ops.get_recipients(bank)
        
        # Check if the response is JSON
        if response.headers['Content-Type'] != 'application/json':
            self.fail(f"Expected JSON response but got {response.headers['Content-Type']}.\nResponse content: {response.content.decode('utf-8')}")

        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed to get recipients for bank {bank}.")
        
        recipients = response.json()
        recipient_ids = [recipient['recipient_id'] for recipient in recipients]
        self.assertIn(recipient_id, recipient_ids, f"Recipient ID {recipient_id} not found in response.")