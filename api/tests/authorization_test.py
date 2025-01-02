import os
import json
from django.test import TestCase
from rest_framework import status

from api.operations import ContractOperations, PartyOperations
from api.operations import SettlementOperations, TransactionOperations

from api.managers import SecretsManager, ConfigManager

class AuthorizationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        contract_file = os.path.join(os.path.dirname(__file__), 'fixtures', 'authorization_test', 'authorization.json')
        with open(contract_file, 'r') as file:
            cls.contract_data = json.load(file)

    def setUp(self):
        self.secrets_manager = SecretsManager()
        self.config_manager = ConfigManager()

        self.keys = self.secrets_manager.load_keys()  
        self.config = self.config_manager.load_config()
        
        self.headers = {
            'Content-Type': 'application/json'
        }

        self.contract_ops = ContractOperations(self.headers, self.config)
        self.party_ops = PartyOperations(self.headers, self.config)
        self.settlement_ops = SettlementOperations(self.headers, self.config)
        self.transaction_ops = TransactionOperations(self.headers, self.config)

    def test_authorization_failures(self):
        # 1. Without authorization
        response = self.contract_ops.load_contract(self.contract_data['contract'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, "Should fail without authorization")

        # 2. Invalid key (e.g., 'XXXXXXX')
        self.headers['Authorization'] = 'Api-Key XXXXXXX'
        response = self.contract_ops.load_contract(self.contract_data['contract'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, "Should fail with invalid key")

        # 3. Affiliate key (from secrets manager, not from api_key.json)
        self.headers['Authorization'] = f"Api-Key {self.keys['Affiliate']}"
        response = self.contract_ops.load_contract(self.contract_data['contract'])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, "Affiliate key should fail with authorization error")

        # 4. Master key (FIZIT_MASTER_KEY)
        self.headers['Authorization'] = f"Api-Key {self.keys['FIZIT_MASTER_KEY']}"
        response = self.contract_ops.load_contract(self.contract_data['contract'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "FIZIT_MASTER_KEY should succeed")

        # Retrieve the created contract ID for further tests
        contract_idx = response.json()

        # 5. Get contract without authorization
        self.headers.pop('Authorization', None)
        response = self.contract_ops.get_contract(contract_idx)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, "Should fail without authorization when retrieving contract")

        # 6. Invalid key
        self.headers['Authorization'] = 'Api-Key XXXXXXX'
        response = self.contract_ops.get_contract(contract_idx)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, "Invalid key should fail when retrieving contract")

        # 7. Affiliate key should retrieve the contract
        self.headers['Authorization'] = f"Api-Key {self.keys['Affiliate']}"
        response = self.contract_ops.get_contract(contract_idx)
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Affiliate key should successfully retrieve contract")

        # 8. Add parties without authorization, invalid key, and Affiliate key
        self.headers.pop('Authorization', None)
        response = self.party_ops.add_parties(contract_idx, self.contract_data['parties'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, "Adding parties should fail without authorization")

        self.headers['Authorization'] = 'Api-Key XXXXXXX'
        response = self.party_ops.add_parties(contract_idx, self.contract_data['parties'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, "Adding parties should fail with invalid key")

        self.headers['Authorization'] = f"Api-Key {self.keys['Affiliate']}"
        response = self.party_ops.add_parties(contract_idx, self.contract_data['parties'])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, "Affiliate key should fail adding parties")

        # FIZIT_MASTER_KEY should succeed
        self.headers['Authorization'] = f"Api-Key {self.keys['FIZIT_MASTER_KEY']}"
        response = self.party_ops.add_parties(contract_idx, self.contract_data['parties'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "FIZIT_MASTER_KEY should succeed in adding parties")

        # 9. Retrieve parties without authorization, invalid key, and Affiliate key
        self.headers.pop('Authorization', None)
        response = self.party_ops.get_parties(contract_idx)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, "Retrieving parties should fail without authorization")

        self.headers['Authorization'] = 'Api-Key XXXXXXX'
        response = self.party_ops.get_parties(contract_idx)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, "Retrieving parties should fail with invalid key")

        self.headers['Authorization'] = f"Api-Key {self.keys['Affiliate']}"
        response = self.party_ops.get_parties(contract_idx)
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Affiliate key should successfully retrieve parties")

        # Repeat steps 8-9 for settlements and transactions

        # Add settlements
        self.headers.pop('Authorization', None)
        response = self.settlement_ops.post_settlements(contract_idx, self.contract_data['settlements'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, "Adding settlements should fail without authorization")

        self.headers['Authorization'] = 'Api-Key XXXXXXX'
        response = self.settlement_ops.post_settlements(contract_idx, self.contract_data['settlements'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, "Adding settlements should fail with invalid key")

        self.headers['Authorization'] = f"Api-Key {self.keys['Affiliate']}"
        response = self.settlement_ops.post_settlements(contract_idx, self.contract_data['settlements'])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, "Affiliate key should fail adding settlements")

        self.headers['Authorization'] = f"Api-Key {self.keys['FIZIT_MASTER_KEY']}"
        response = self.settlement_ops.post_settlements(contract_idx, self.contract_data['settlements'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "FIZIT_MASTER_KEY should succeed in adding settlements")

        # Retrieve settlements
        self.headers.pop('Authorization', None)
        response = self.settlement_ops.get_settlements(contract_idx)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, "Retrieving settlements should fail without authorization")

        self.headers['Authorization'] = 'Api-Key XXXXXXX'
        response = self.settlement_ops.get_settlements(contract_idx)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, "Retrieving settlements should fail with invalid key")

        self.headers['Authorization'] = f"Api-Key {self.keys['Affiliate']}"
        response = self.settlement_ops.get_settlements(contract_idx)
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Affiliate key should successfully retrieve settlements")

        # Add transactions
        self.headers.pop('Authorization', None)
        response = self.transaction_ops.post_transactions(contract_idx, self.contract_data['transactions'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, "Adding transactions should fail without authorization")

        self.headers['Authorization'] = 'Api-Key XXXXXXX'
        response = self.transaction_ops.post_transactions(contract_idx, self.contract_data['transactions'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, "Adding transactions should fail with invalid key")

        self.headers['Authorization'] = f"Api-Key {self.keys['Affiliate']}"
        response = self.transaction_ops.post_transactions(contract_idx, self.contract_data['transactions'])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, "Affiliate key should fail adding transactions")

        self.headers['Authorization'] = f"Api-Key {self.keys['FIZIT_MASTER_KEY']}"
        response = self.transaction_ops.post_transactions(contract_idx, self.contract_data['transactions'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "FIZIT_MASTER_KEY should succeed in adding transactions")

        # Retrieve transactions
        self.headers.pop('Authorization', None)
        response = self.transaction_ops.get_transactions(contract_idx)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, "Retrieving transactions should fail without authorization")

        self.headers['Authorization'] = 'Api-Key XXXXXXX'
        response = self.transaction_ops.get_transactions(contract_idx)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, "Retrieving transactions should fail with invalid key")

        self.headers['Authorization'] = f"Api-Key {self.keys['Affiliate']}"
        response = self.transaction_ops.get_transactions(contract_idx)
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Affiliate key should successfully retrieve transactions")

        print("All authorization tests passed.")