import os
import json
import time

from decimal import Decimal
from datetime import datetime

from django.test import TestCase
from rest_framework import status

import packages.load_keys as load_keys
import packages.load_config as load_config

from .utils import Utils
from .payment_operations import PaymentOperations
from .contract_operations import ContractOperations
from .party_operations import PartyOperations
from .settlement_operations import SettlementOperations
from .transaction_operations import TransactionOperations

keys = load_keys.load_keys()
config = load_config.load_config()

class PayAdvanceTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        self.current_date = datetime.now().replace(microsecond=0).isoformat()
        self.headers = {
            'Authorization': f'Api-Key {keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }
        self.payment_ops = PaymentOperations(self.headers, config)
        self.contract_ops = ContractOperations(self.headers, config)
        self.party_ops = PartyOperations(self.headers, config)
        self.settlement_ops = SettlementOperations(self.headers, config)
        self.transaction_ops = TransactionOperations(self.headers, config)
        self.utils = Utils(self.headers, config)

    def test_pay_advance(self):
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_pay_advance')
        for filename in os.listdir(fixtures_dir):
            if filename.endswith('.json'):
                with open(os.path.join(fixtures_dir, filename), 'r') as file:
                    try:
                        data = json.load(file)
                        print(f"Loading contract data from file: {filename}")
                        contract_idx = self._test_create_contract(data['contract'])
                        self._test_load_parties(contract_idx, data['parties'])
                        print (f"Parties loaded for contract: {contract_idx}")
                        self._test_load_settlements(contract_idx, data['settlements'])
                        print (f"Settlements loaded for contract: {contract_idx}")
                        self._test_load_transactions(contract_idx, data['transactions'])
                        print (f"Transactions loaded for contract: {contract_idx}")
                        self._test_get_advance(contract_idx, data['contract'])
                    except json.JSONDecodeError as e:
                        self.fail(f'Error decoding JSON from file: {filename}, Error: {str(e)}')
                    except KeyError as e:
                        self.fail(f'Missing key in JSON from file: {filename}, Error: {str(e)}')

    def _test_create_contract(self, contract_data):
        response = self.contract_ops.load_contract(contract_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Failed to create contract.")
        contract_idx = response.json()
        self.assertIsNotNone(contract_idx, 'Contract index should not be None')
        print(f'Successfully added contract {contract_idx}')
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

    def _test_get_advance(self, contract_idx, contract_data):
            expected_advance_count = contract_data["extended_data"].get("advance_count")

            # First, get the advances
            response = self.payment_ops.get_advance(contract_idx)
            print(f"Advances loaded for contract: {contract_idx}")
            self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed to get advance amount for contract {contract_idx}.")

            advances = response.json()  
            self.assertEqual(
                len(advances),
                expected_advance_count,
                f"Expected advance count {expected_advance_count} does not match actual count {len(advances)} for contract {contract_idx}."
            )

            # Now, call the payment_ops.add_advance function with the advances
            csrf_token = self.utils._get_csrf_token()
            add_advance_response = self.payment_ops.add_advance(contract_idx, advances, csrf_token)
            self.assertEqual(
                add_advance_response.status_code, 
                status.HTTP_201_CREATED,
                f"Failed to add advances for contract {contract_idx}. Status code: {add_advance_response.status_code}\nResponse: {add_advance_response.text}"
            )

            print(f"Successfully added advances for contract: {contract_idx}")

            # Wait for 15 seconds
            time.sleep(15)

            # Get the advances again after the delay
            response = self.payment_ops.get_advance(contract_idx)
            self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed to get advance amount for contract {contract_idx} after waiting.")

            advances_after_payment = response.json()
            self.assertEqual(
                len(advances_after_payment),
                0,
                f"Expected advance count to be 0 after payment, but got {len(advances_after_payment)} for contract {contract_idx}."
            )

            print(f"Advances successfully processed and cleared for contract: {contract_idx}")