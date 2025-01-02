import os
import json
from django.test import TestCase
from rest_framework import status

from api.operations import ContractOperations, PartyOperations
from api.operations import SettlementOperations, TransactionOperations

from api.managers import SecretsManager, ConfigManager

class EncryptionTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Load the authorization.json and noauth.json files
        base_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'encryption_test')
        authorization_file = os.path.join(base_dir, 'party.json')
        noauth_file = os.path.join(base_dir, 'noparty.json')

        with open(authorization_file, 'r') as file:
            cls.authorization_contract_data = json.load(file)

        with open(noauth_file, 'r') as file:
            cls.noauth_contract_data = json.load(file)

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

        # Load authorization and noauth contracts with FIZIT_MASTER_KEY before running individual tests
        self.headers['Authorization'] = f"Api-Key {self.keys['FIZIT_MASTER_KEY']}"

        # Load authorization contract
        response = self.contract_ops.load_contract(self.authorization_contract_data['contract'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "FIZIT_MASTER_KEY should succeed loading authorization contract")
        self.authorization_contract_idx = response.json()  # Capture the contract_idx

        # Add parties, settlements, and transactions for authorization contract
        response = self.party_ops.add_parties(self.authorization_contract_idx, self.authorization_contract_data['parties'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "FIZIT_MASTER_KEY should succeed adding parties to authorization contract")

        response = self.settlement_ops.post_settlements(self.authorization_contract_idx, self.authorization_contract_data['settlements'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "FIZIT_MASTER_KEY should succeed adding settlements to authorization contract")

        response = self.transaction_ops.post_transactions(self.authorization_contract_idx, self.authorization_contract_data['transactions'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "FIZIT_MASTER_KEY should succeed adding transactions to authorization contract")

        # Load noauth contract
        response = self.contract_ops.load_contract(self.noauth_contract_data['contract'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "FIZIT_MASTER_KEY should succeed loading noauth contract")
        self.noauth_contract_idx = response.json()  # Capture the contract_idx

        # Add parties, settlements, and transactions for noauth contract
        response = self.party_ops.add_parties(self.noauth_contract_idx, self.noauth_contract_data['parties'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "FIZIT_MASTER_KEY should succeed adding parties to noauth contract")

        response = self.settlement_ops.post_settlements(self.noauth_contract_idx, self.noauth_contract_data['settlements'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "FIZIT_MASTER_KEY should succeed adding settlements to noauth contract")

        response = self.transaction_ops.post_transactions(self.noauth_contract_idx, self.noauth_contract_data['transactions'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "FIZIT_MASTER_KEY should succeed adding transactions to noauth contract")

    def test_supplier_key_contract_decryption(self):
        # Get authorization contract using Affiliate API key
        self.headers['Authorization'] = f"Api-Key {self.keys['Affiliate']}"
        response = self.contract_ops.get_contract(self.authorization_contract_idx)
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Affiliate key should retrieve authorization contract")

        # Check if extended_data and transact_logic are decrypted
        contract_data = response.json()
        self.assertNotEqual(contract_data['extended_data'], "encrypted data", "extended_data should be decrypted")
        self.assertNotEqual(contract_data['transact_logic'], "encrypted data", "transact_logic should be decrypted")

    def test_affiliate_key_contract_noauth(self):
        # Get noauth contract using Affiliate API key
        self.headers['Authorization'] = f"Api-Key {self.keys['Affiliate']}"
        response = self.contract_ops.get_contract(self.noauth_contract_idx)
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Affiliate key should retrieve noauth contract")

        # Check if extended_data and transact_logic are returned as "encrypted data"
        contract_data = response.json()
        self.assertEqual(contract_data['extended_data'], "encrypted data", "extended_data should not be decrypted")
        self.assertEqual(contract_data['transact_logic'], "encrypted data", "transact_logic should not be decrypted")

    def test_affiliate_key_settlement_decryption(self):
        # Get authorization settlements using Affiliate API key
        self.headers['Authorization'] = f"Api-Key {self.keys['Affiliate']}"
        response = self.settlement_ops.get_settlements(self.authorization_contract_idx)
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Affiliate key should retrieve authorization settlements")

        # Check if extended_data is decrypted
        settlements_data = response.json()
        self.assertNotEqual(settlements_data[0]['extended_data'], "encrypted data", "extended_data should be decrypted")

    def test_affiliate_key_settlement_noauth(self):
        # Get noauth settlements using Affiliate API key
        self.headers['Authorization'] = f"Api-Key {self.keys['Affiliate']}"
        response = self.settlement_ops.get_settlements(self.noauth_contract_idx)
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Affiliate key should retrieve noauth settlements")

        # Check if extended_data is returned as "encrypted data"
        settlements_data = response.json()
        self.assertEqual(settlements_data[0]['extended_data'], "encrypted data", "extended_data should not be decrypted")

    def test_affiliate_key_transaction_decryption(self):
        # Get authorization transactions using Affiliate API key
        self.headers['Authorization'] = f"Api-Key {self.keys['Affiliate']}"
        response = self.transaction_ops.get_transactions(self.authorization_contract_idx)
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Affiliate key should retrieve authorization transactions")

        # Check if transact_data and extended_data are decrypted
        transactions_data = response.json()
        self.assertNotEqual(transactions_data[0]['transact_data'], "encrypted data", "transact_data should be decrypted")
        self.assertNotEqual(transactions_data[0]['extended_data'], "encrypted data", "extended_data should be decrypted")

    def test_affiliate_key_transaction_noauth(self):
        # Get noauth transactions using Affiliate API key
        self.headers['Authorization'] = f"Api-Key {self.keys['Affiliate']}"
        response = self.transaction_ops.get_transactions(self.noauth_contract_idx)
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Affiliate key should retrieve noauth transactions")

        # Check if transact_data and extended_data are returned as "encrypted data"
        transactions_data = response.json()
        self.assertEqual(transactions_data[0]['transact_data'], "encrypted data", "transact_data should not be decrypted")
        self.assertEqual(transactions_data[0]['extended_data'], "encrypted data", "extended_data should not be decrypted")

        print("All decryption and noauth tests passed.")