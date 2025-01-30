import os
import json
import logging
from django.test import TestCase
from rest_framework import status

from api.operations import ContractOperations, PartyOperations, CsrfOperations
from api.operations import SettlementOperations, TransactionOperations
from api.secrets import SecretsManager
from api.config import ConfigManager
from api.utilities.logging import log_info, log_warning, log_error

class EncryptionTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        """Load test data from fixtures."""
        base_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'encryption')

        cls.authorization_contract_data = cls._load_json(os.path.join(base_dir, 'party_encrypt.json'))
        cls.noauth_contract_data = cls._load_json(os.path.join(base_dir, 'noparty_encrypt.json'))

        cls.logger = logging.getLogger(__name__)

    def setUp(self):
        """Set up test environment and initialize required components."""
        self.secrets_manager = SecretsManager()
        self.config_manager = ConfigManager()

        self.headers = {'Content-Type': 'application/json'}

        self.csrf_ops = CsrfOperations(self.headers, self.config_manager.get_base_url())
        self.csrf_token = self.csrf_ops.get_csrf_token()

        self.contract_ops = ContractOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.party_ops = PartyOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.settlement_ops = SettlementOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.transaction_ops = TransactionOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)

        self._load_test_contracts()

    def test_supplier_key_contract_decryption(self):
        """Test contract decryption with a supplier key."""
        self._test_decryption(
            operation=self.contract_ops.get_contract,
            contract_type=self.authorization_contract_type,
            contract_idx=self.authorization_contract_idx,
            key='Affiliate',
            fields_to_check=['extended_data', 'transact_logic'],
            should_decrypt=True,
            data_type="authorization contract"
        )

    def test_affiliate_key_contract_noauth(self):
        """Test unauthorized contract decryption with an affiliate key."""
        self._test_decryption(
            operation=self.contract_ops.get_contract,
            contract_type=self.noauth_contract_type,
            contract_idx=self.noauth_contract_idx,
            key='Affiliate',
            fields_to_check=['extended_data', 'transact_logic'],
            should_decrypt=False,
            data_type="noauth contract"
        )

    def test_affiliate_key_settlement_decryption(self):
        """Test settlement decryption with an affiliate key."""
        self._test_decryption(
            operation=self.settlement_ops.get_settlements,
            contract_type=self.authorization_contract_type,
            contract_idx=self.authorization_contract_idx,
            key='Affiliate',
            fields_to_check=['extended_data'],
            should_decrypt=True,
            data_type="authorization settlements"
        )

    def test_affiliate_key_settlement_noauth(self):
        """Test unauthorized settlement decryption with an affiliate key."""
        self._test_decryption(
            operation=self.settlement_ops.get_settlements,
            contract_type=self.noauth_contract_type,
            contract_idx=self.noauth_contract_idx,
            key='Affiliate',
            fields_to_check=['extended_data'],
            should_decrypt=False,
            data_type="noauth settlements"
        )

    def test_affiliate_key_transaction_decryption(self):
        """Test transaction decryption with an affiliate key."""
        self._test_decryption(
            operation=self.transaction_ops.get_transactions,
            contract_type=self.authorization_contract_type,
            contract_idx=self.authorization_contract_idx,
            key='Affiliate',
            fields_to_check=['transact_data', 'extended_data'],
            should_decrypt=True,
            data_type="authorization transactions"
        )

    def test_affiliate_key_transaction_noauth(self):
        """Test unauthorized transaction decryption with an affiliate key."""
        self._test_decryption(
            operation=self.transaction_ops.get_transactions,
            contract_type=self.noauth_contract_type,
            contract_idx=self.noauth_contract_idx,
            key='Affiliate',
            fields_to_check=['transact_data', 'extended_data'],
            should_decrypt=False,
            data_type="noauth transactions"
        )

    def _load_test_contracts(self):
        """Load test contracts and set up related data."""
        log_info(self.logger, "Loading authorization contract...")
        self.authorization_contract_idx, self.authorization_contract_type = self._load_contract(self.authorization_contract_data)
        
        log_info(self.logger, "Loading noauth contract...")
        self.noauth_contract_idx, self.noauth_contract_type = self._load_contract(self.noauth_contract_data)

    def _load_contract(self, contract_data):
        """Helper to load contract data and related entities."""
        contract_type = contract_data["contract_type"]  # Extract contract_type dynamically
        log_info(self.logger, f"Processing contract of type: {contract_type}")

        self.headers['Authorization'] = f"Api-Key {self.secrets_manager.get_master_key()}"
        response = self.contract_ops.post_contract(contract_type, contract_data['contract'])

        contract_idx = response["contract_idx"]

        self._add_entities(contract_type, contract_idx, contract_data)
        return contract_idx, contract_type

    def _add_entities(self, contract_type, contract_idx, contract_data):
        """Add parties, settlements, and transactions to a contract."""
        self._add_entity(self.party_ops.post_parties, contract_type, contract_idx, contract_data['parties'], f"{contract_type} parties")
        self._add_entity(self.settlement_ops.post_settlements, contract_type, contract_idx, contract_data['settlements'], f"{contract_type} settlements")
        self._add_entity(self.transaction_ops.post_transactions, contract_type, contract_idx, contract_data['transactions'], f"{contract_type} transactions")

    def _add_entity(self, operation, contract_type, contract_idx, data, entity_name):
        """Generic method to add contract-related entities."""
        response = operation(contract_type, contract_idx, data)
        log_info(self.logger, f"Loaded {response.get('count', 0)} {entity_name} for contract {contract_idx}")

    def _test_decryption(self, operation, contract_type, contract_idx, key, fields_to_check, should_decrypt, data_type):
        """Test decryption logic for a given entity."""
        self.headers['Authorization'] = f"Api-Key {self.secrets_manager.get_partner_api_key(key)}"

        data = operation(contract_type, contract_idx)
        log_info(self.logger, f"Data {data}")
        log_info(self.logger, f"Operation {operation}")
        log_info(self.logger, f"Contract type {contract_type}")
        log_info(self.logger, f"Contract idx {contract_idx}")
        log_info(self.logger, f"Key {key}")
        log_info(self.logger, f"Fields to check {fields_to_check}")
        log_info(self.logger, f"Should decrypt {should_decrypt}")

        for field in fields_to_check:
            expected = "encrypted data" if not should_decrypt else "decrypted"
            actual = data[0][field] if isinstance(data, list) else data[field]
            condition = actual != "encrypted data" if should_decrypt else actual == "encrypted data"
            self.assertTrue(condition, f"{field} should be {expected}.")

    @staticmethod
    def _load_json(filepath):
        """Helper to load JSON data from a file."""
        with open(filepath, 'r') as file:
            return json.load(file)