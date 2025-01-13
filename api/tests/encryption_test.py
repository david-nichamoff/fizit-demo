import os
import json
import logging
from django.test import TestCase
from rest_framework import status

from api.operations import ContractOperations, PartyOperations, CsrfOperations
from api.operations import SettlementOperations, TransactionOperations
from api.managers import SecretsManager, ConfigManager

from api.utilities.logging import log_info, log_warning, log_error

class EncryptionTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        base_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'encryption_test')

        cls.authorization_contract_data = cls._load_json(os.path.join(base_dir, 'party.json'))
        cls.noauth_contract_data = cls._load_json(os.path.join(base_dir, 'noparty.json'))

        cls.logger = logging.getLogger(__name__)

    def setUp(self):
        self.secrets_manager = SecretsManager()
        self.config_manager = ConfigManager()

        self.keys = self.secrets_manager.load_keys()
        self.config = self.config_manager.load_config()
        self.headers = {'Content-Type': 'application/json'}

        self.csrf_ops = CsrfOperations(self.headers, self.config)
        self.csrf_token = self.csrf_ops.get_csrf_token()

        self.contract_ops = ContractOperations(self.headers, self.config, self.csrf_token)
        self.party_ops = PartyOperations(self.headers, self.config, self.csrf_token)
        self.settlement_ops = SettlementOperations(self.headers, self.config, self.csrf_token)
        self.transaction_ops = TransactionOperations(self.headers, self.config, self.csrf_token)

        self._load_test_contracts()

    def test_supplier_key_contract_decryption(self):
        self._test_decryption(
            operation=self.contract_ops.get_contract,
            contract_idx=self.authorization_contract_idx,
            key='Affiliate',
            fields_to_check=['extended_data', 'transact_logic'],
            should_decrypt=True,
            data_type="authorization contract"
        )

#    def test_affiliate_key_contract_noauth(self):
#        self._test_decryption(
#            operation=self.contract_ops.get_contract,
#            contract_idx=self.noauth_contract_idx,
#            key='Affiliate',
#            fields_to_check=['extended_data', 'transact_logic'],
#            should_decrypt=False,
#            data_type="noauth contract"
#        )
#
#    def test_affiliate_key_settlement_decryption(self):
#        self._test_decryption(
#            operation=self.settlement_ops.get_settlements,
#            contract_idx=self.authorization_contract_idx,
#            key='Affiliate',
#            fields_to_check=['extended_data'],
#            should_decrypt=True,
#            data_type="authorization settlements"
#        )
#
#    def test_affiliate_key_settlement_noauth(self):
#        self._test_decryption(
#            operation=self.settlement_ops.get_settlements,
#            contract_idx=self.noauth_contract_idx,
#            key='Affiliate',
#            fields_to_check=['extended_data'],
#            should_decrypt=False,
#            data_type="noauth settlements"
#        )
#
#    def test_affiliate_key_transaction_decryption(self):
#        self._test_decryption(
#            operation=self.transaction_ops.get_transactions,
#            contract_idx=self.authorization_contract_idx,
#            key='Affiliate',
#            fields_to_check=['transact_data', 'extended_data'],
#            should_decrypt=True,
#            data_type="authorization transactions"
#        )
#
#    def test_affiliate_key_transaction_noauth(self):
#        self._test_decryption(
##            operation=self.transaction_ops.get_transactions,
#            contract_idx=self.noauth_contract_idx,
#            key='Affiliate',
#            fields_to_check=['transact_data', 'extended_data'],
#            should_decrypt=False,
#            data_type="noauth transactions"
#        )
#
    def _load_test_contracts(self):
        """Load test contracts and set up related data."""
        log_info(self.logger, "Loading authorization contract...")
        self.authorization_contract_idx = self._load_contract(self.authorization_contract_data, "authorization")
        log_info(self.logger, "Loading noauth contract...")
        self.noauth_contract_idx = self._load_contract(self.noauth_contract_data, "noauth")

    def _load_contract(self, contract_data, contract_type):
        """Helper to load contract data and related entities."""
        self.headers['Authorization'] = f"Api-Key {self.keys['FIZIT_MASTER_KEY']}"
        response = self.contract_ops.post_contract(contract_data['contract'])
        contract_idx = response["contract_idx"]

        self._add_entities(contract_idx, contract_data, contract_type)
        return contract_idx

    def _add_entities(self, contract_idx, contract_data, contract_type):
        """Add parties, settlements, and transactions to a contract."""
        self._add_entity(self.party_ops.post_parties, contract_idx, contract_data['parties'], f"{contract_type} parties")
        self._add_entity(self.settlement_ops.post_settlements, contract_idx, contract_data['settlements'], f"{contract_type} settlements")
        self._add_entity(self.transaction_ops.post_transactions, contract_idx, contract_data['transactions'], f"{contract_type} transactions")

    def _add_entity(self, operation, contract_idx, data, entity_name):
        response = operation(contract_idx, data)
        log_info(self.logger, f"Loaded {response["count"]} {entity_name} for contract {contract_idx}")

    def _test_decryption(self, operation, contract_idx, key, fields_to_check, should_decrypt, data_type):
        self.headers['Authorization'] = f"Api-Key {self.keys[key]}"

        data = operation(contract_idx)

        for field in fields_to_check:
            expected = "encrypted data" if not should_decrypt else "decrypted"
            actual = data[0][field] if isinstance(data, list) else data[field]
            condition = actual != "encrypted data" if should_decrypt else actual == "encrypted data"
            self.assertTrue(condition, f"{field} should be {expected}.")

    @staticmethod
    def _load_json(filepath):
        """Helper to load JSON data."""
        with open(filepath, 'r') as file:
            return json.load(file)