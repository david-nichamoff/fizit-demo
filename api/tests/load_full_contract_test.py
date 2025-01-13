import os
import json
import logging

from django.test import TestCase

from api.operations import (
    ContractOperations, PartyOperations, SettlementOperations,
    TransactionOperations, ArtifactOperations, CsrfOperations
)
from api.managers import SecretsManager, ConfigManager

from api.utilities.logging import log_info, log_warning, log_error

class FullContractTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        """Set up shared data for all test cases."""
        cls.secrets_manager = SecretsManager()
        cls.config_manager = ConfigManager()

        cls.keys = cls.secrets_manager.load_keys()
        cls.config = cls.config_manager.load_config()

    def setUp(self):
        """Set up resources for each individual test."""
        self.headers = {
            'Authorization': f'Api-Key {self.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }

        self.logger = logging.getLogger(__name__)

        self.csrf_ops = CsrfOperations(self.headers, self.config)
        self.csrf_token = self.csrf_ops.get_csrf_token()

        self.contract_ops = ContractOperations(self.headers, self.config, self.csrf_token)
        self.party_ops = PartyOperations(self.headers, self.config, self.csrf_token)
        self.settlement_ops = SettlementOperations(self.headers, self.config, self.csrf_token)
        self.transaction_ops = TransactionOperations(self.headers, self.config, self.csrf_token)
        self.artifact_ops = ArtifactOperations(self.headers, self.config, self.csrf_token)

    def test_load_contract(self):
        """Load and test all contracts from the fixtures directory."""
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'full_contract_test')
        log_info(self.logger, f"Loading contracts from directory: {fixtures_dir}")

        for filename in self._get_json_files(fixtures_dir):
            try:
                contract_data = self._load_fixture(os.path.join(fixtures_dir, filename))
                log_info(self.logger, f"Processing contract from file: {filename}")
                self._process_contract(contract_data)
            except (json.JSONDecodeError, KeyError) as e:
                self.fail(f"Error processing file {filename}: {e}")

    def _process_contract(self, data):
        """Process a single contract and its associated entities."""
        contract_idx = self._load_entity(
            operation=self.contract_ops.post_contract,
            data=data['contract'],
            entity_name="contract"
        )

        if 'parties' in data:
            self._load_entity(
                operation=self.party_ops.post_parties,
                data=data['parties'],
                contract_idx=contract_idx,
                entity_name="parties"
            )

        if 'settlements' in data:
            self._load_entity(
                operation=self.settlement_ops.post_settlements,
                data=data['settlements'],
                contract_idx=contract_idx,
                entity_name="settlements"
            )

        if 'transactions' in data:
            self._load_entity(
                operation=self.transaction_ops.post_transactions,
                data=data['transactions'],
                contract_idx=contract_idx,
                entity_name="transactions"
            )

        if 'artifacts' in data:
            self._load_entity(
                operation=self.artifact_ops.post_artifacts,
                data=data['artifacts'],
                contract_idx=contract_idx,
                entity_name="artifacts",
            )

    def _load_entity(self, operation, data, entity_name, contract_idx=None):
        """Generic method to load entities (e.g., parties, settlements, transactions, artifacts)."""

        response = operation(contract_idx, data) if contract_idx else operation(data)
        
        log_info(self.logger, f"Response from add {entity_name}: {response}")

        if entity_name == "contract":
            self.assertGreaterEqual(response.get("contract_idx", -1), 0)
            return response["contract_idx"]
        else:
            self.assertGreaterEqual(response.get("count", 0), 1)

    def _load_fixture(self, filepath):
        """Load a JSON fixture file."""
        with open(filepath, 'r') as file:
            return json.load(file)

    def _get_json_files(self, directory):
        """Retrieve all JSON files from a directory."""
        return [f for f in os.listdir(directory) if f.endswith('.json')]
