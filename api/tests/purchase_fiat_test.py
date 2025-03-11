import os
import json
import time
import logging
from datetime import datetime

from django.test import TestCase

from api.secrets import SecretsManager
from api.config import ConfigManager
from api.registry import RegistryManager
from api.operations import (
    ContractOperations, PartyOperations, TransactionOperations,
    CsrfOperations, BankOperations
)

from api.utilities.logging import log_info, log_error

class PurchaseFiatTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.logger = logging.getLogger(__name__)
        cls.secrets_manager = SecretsManager()
        cls.config_manager = ConfigManager()
        cls.registry_manager = RegistryManager()

    def setUp(self):
        self.headers = {
            'Authorization': f'Api-Key {self.secrets_manager.get_master_key()}',
            'Content-Type': 'application/json'
        }
        self.current_date = datetime.now().replace(microsecond=0).isoformat()

        self.csrf_ops = CsrfOperations(self.headers, self.config_manager.get_base_url())
        self.csrf_token = self.csrf_ops.get_csrf_token()

        # Initialize operations
        self.payment_ops = BankOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.contract_ops = ContractOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.party_ops = PartyOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.transaction_ops = TransactionOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)

    def test_purchase_payments(self):
        """Test full lifecycle of a purchase contract: create, add transactions, and process advances."""
        filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'purchase_fiat.json')
        log_info(self.logger, "Starting purchase payment tests...")

        with open(filename, 'r') as file:
            contract_data = json.load(file)

        try:
            contract_type = contract_data["contract_type"]
            contract_idx = self._test_create_contract(contract_type, contract_data['contract'])
            self._load_entities(contract_type, contract_idx, contract_data)

            self._test_get_advances(contract_type, contract_idx, contract_data['contract'])

        except json.JSONDecodeError as e:
            self.fail(f"Error decoding JSON from {filename}: {str(e)}")
        except KeyError as e:
            self.fail(f"Missing key in JSON from {filename}: {str(e)}")

    def _load_entities(self, contract_type, contract_idx, data):
        """Load parties and transactions into the contract."""
        self._test_load_parties(contract_type, contract_idx, data['parties'])
        self._test_load_transactions(contract_type, contract_idx, data['transactions'])

    def _test_create_contract(self, contract_type, contract_data):
        """Create the purchase contract."""
        contract_data["contract_name"] = "Purchase Fiat Test"
        response = self.contract_ops.post_contract(contract_type, contract_data)
        contract_idx = response.get("contract_idx")
        self.assertGreater(contract_idx, 0)
        log_info(self.logger, f"Added purchase contract: {contract_idx}")
        return contract_idx

    def _test_load_parties(self, contract_type, contract_idx, parties_data):
        """Load parties into the contract."""
        response = self.party_ops.post_parties(contract_type, contract_idx, parties_data)
        log_info(self.logger, f"Response from load_parties: {response}")
        self.assertGreater(response['count'], 0)
        log_info(self.logger, f"Parties loaded for contract {contract_idx}")

    def _test_load_transactions(self, contract_type, contract_idx, transactions_data):
        """Load transactions into the contract."""
        response = self.transaction_ops.post_transactions(contract_type, contract_idx, transactions_data)
        log_info(self.logger, f"Response from load_transactions: {response}")
        self.assertGreater(response['count'], 0)
        log_info(self.logger, f"Transactions loaded for contract {contract_idx}")

    def _test_get_advances(self, contract_type, contract_idx, contract_data):
        """Retrieve and process advances for the purchase contract."""
        advances = self.payment_ops.get_advances(contract_type, contract_idx)
        log_info(self.logger, f"Advances loaded for contract {contract_type}:{contract_idx}: {advances}")
        transactions = self.transaction_ops.get_transactions(contract_type, contract_idx)

        self.assertEqual(len(advances), len(transactions), 
                         f"Expected {len(transactions)} advances but got {len(advances)} for contract {contract_idx}.")
        
        self._process_advances(contract_type, contract_idx, advances)

    def _process_advances(self, contract_type, contract_idx, advances):
        """Process advances by posting them."""
        response = self.payment_ops.post_advances(contract_type, contract_idx, advances)
        log_info(self.logger, f"Response from process_advances: {response}")
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Advances processed for contract {contract_idx}. Waiting for processing...")
        time.sleep(10)