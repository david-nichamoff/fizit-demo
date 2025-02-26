import os
import json
import time
import logging
import uuid
from datetime import datetime

from django.test import TestCase

from api.secrets import SecretsManager
from api.config import ConfigManager
from api.registry import RegistryManager
from api.operations import (
    ContractOperations, PartyOperations, SettlementOperations,
    TransactionOperations, CsrfOperations, BankOperations
)

from api.utilities.logging import log_info, log_error


class SaleManualTest(TestCase):
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
        self.settlement_ops = SettlementOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.transaction_ops = TransactionOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)

    def test_manual_sale_payments(self):
        """Test full lifecycle of a manual sale contract: create, add transactions, load settlements, process deposits, and process distributions."""
        filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'sale_manual.json')
        log_info(self.logger, "Starting manual sale contract tests...")

        with open(filename, 'r') as file:
            contract_data = json.load(file)

        try:
            contract_type = contract_data["contract_type"]
            contract_idx = self._test_create_contract(contract_type, contract_data['contract'])
            self._load_entities(contract_type, contract_idx, contract_data)

            self._test_post_deposits(contract_type, contract_idx, contract_data["deposits"])
            self._test_get_distributions(contract_type, contract_idx)

        except json.JSONDecodeError as e:
            self.fail(f"Error decoding JSON from {filename}: {str(e)}")
        except KeyError as e:
            self.fail(f"Missing key in JSON from {filename}: {str(e)}")

    def _load_entities(self, contract_type, contract_idx, data):
        """Load parties, settlements, and transactions into the contract."""
        self._test_load_parties(contract_type, contract_idx, data['parties'])
        self._test_load_settlements(contract_type, contract_idx, data['settlements'])
        self._test_load_transactions(contract_type, contract_idx, data['transactions'])

    def _test_create_contract(self, contract_type, contract_data):
        """Create the manual sale contract."""
        response = self.contract_ops.post_contract(contract_type, contract_data)
        contract_idx = response.get("contract_idx")
        self.assertGreater(contract_idx, 0)
        log_info(self.logger, f"Added sale contract: {contract_idx}")
        return contract_idx

    def _test_load_parties(self, contract_type, contract_idx, parties_data):
        """Load parties into the contract."""
        response = self.party_ops.post_parties(contract_type, contract_idx, parties_data)
        log_info(self.logger, f"Response from load_parties: {response}")
        self.assertGreater(response['count'], 0)
        log_info(self.logger, f"Parties loaded for contract {contract_idx}")

    def _test_load_settlements(self, contract_type, contract_idx, settlements_data):
        """Load settlements into the contract."""
        response = self.settlement_ops.post_settlements(contract_type, contract_idx, settlements_data)
        log_info(self.logger, f"Response from load_settlements: {response}")
        self.assertGreater(response['count'], 0)
        log_info(self.logger, f"Settlements loaded for contract {contract_idx}")

    def _test_load_transactions(self, contract_type, contract_idx, transactions_data):
        """Load transactions into the contract."""
        response = self.transaction_ops.post_transactions(contract_type, contract_idx, transactions_data)
        log_info(self.logger, f"Response from load_transactions: {response}")
        self.assertGreater(response['count'], 0)
        log_info(self.logger, f"Transactions loaded for contract {contract_idx}")

    def _test_post_deposits(self, contract_type, contract_idx, deposit_data):
        """Post deposits directly from sale_manual.json (no retrieval needed)."""
        log_info(self.logger, f"Posting deposits for contract {contract_idx}: {deposit_data}")
        
        response = self.payment_ops.post_deposit(contract_type, contract_idx, deposit_data)
        log_info(self.logger, f"Response from post_deposit: {response}")
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Deposits added for contract {contract_idx}.")

    def _test_get_distributions(self, contract_type, contract_idx):
        """Retrieve and process distributions for the sale contract."""
        distributions = self.payment_ops.get_distributions(contract_type, contract_idx)
        log_info(self.logger, f"Distributions retrieved for contract {contract_idx}: {distributions}")

        # Assign a random tx_hash to each distribution before posting
        for distribution in distributions:
            distribution["tx_hash"] = self._generate_tx_hash()

        # Process the retrieved distributions
        response = self.payment_ops.post_distributions(contract_type, contract_idx, distributions)
        log_info(self.logger, f"Response from post_distributions: {response}")
        self.assertGreater(response["count"], 0, f"Expected distributions to be processed but got {response}")
        log_info(self.logger, f"Distributions processed for contract {contract_idx}. Waiting for processing...")
        time.sleep(10)

    def _generate_tx_hash(self):
        """Generate a random transaction hash."""
        return uuid.uuid4().hex