import os
import json
import logging
import time

from django.test import TestCase

from api.operations import (
    ContractOperations, PartyOperations, SettlementOperations,
    TransactionOperations, ArtifactOperations, CsrfOperations
)
from api.config import ConfigManager
from api.secrets import SecretsManager
from api.utilities.logging import log_info, log_error


class FullContractTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        """Set up shared test data for all cases."""
        cls.logger = logging.getLogger(__name__)
        cls.secrets_manager = SecretsManager()
        cls.config_manager = ConfigManager()

    def setUp(self):
        """Set up authentication headers and initialize API operations."""
        self.headers = {
            'Authorization': f'Api-Key {self.secrets_manager.get_master_key()}',
            'Content-Type': 'application/json'
        }
        self.base_url = self.config_manager.get_base_url()

        self.csrf_ops = CsrfOperations(self.headers, self.base_url)
        self.csrf_token = self.csrf_ops.get_csrf_token()

        self.contract_ops = ContractOperations(self.headers, self.base_url, self.csrf_token)
        self.party_ops = PartyOperations(self.headers, self.base_url, self.csrf_token)
        self.settlement_ops = SettlementOperations(self.headers, self.base_url, self.csrf_token)
        self.transaction_ops = TransactionOperations(self.headers, self.base_url, self.csrf_token)
        self.artifact_ops = ArtifactOperations(self.headers, self.base_url, self.csrf_token)

    def test_full_contract_workflow(self):
        """Test full contract lifecycle: create contract, add parties, settlements, transactions, and artifacts."""
        fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures", "full_contract")
        filenames = self._get_json_files(fixtures_dir)

        if not filenames:
            self.fail("No test files found in fixtures/full_contract_test")

        for filename in filenames:
            file_path = os.path.join(fixtures_dir, filename)
            contract_data = self._load_json(file_path)

            contract_type = contract_data["contract_type"]
            contract_body = contract_data["contract_data"]
            party_list = contract_data.get("parties", [])
            settlement_list = contract_data.get("settlements", [])
            transaction_list = contract_data.get("transactions", [])
            artifact_urls = contract_data.get("artifacts", [])

            log_info(self.logger, f"Processing contract {contract_type} from {filename}")

            # Step 1: Create contract
            create_response = self.contract_ops.post_contract(contract_type, contract_body)

            if "error" in create_response:
                self.fail(f"Failed to create contract from {filename}: {create_response}")

            self.assertIn("contract_idx", create_response, "Response must contain 'contract_idx'")
            contract_idx = create_response["contract_idx"]
            self.assertIsInstance(contract_idx, int, "Contract index must be an integer")

            log_info(self.logger, f"Created contract {contract_type}:{contract_idx} from {filename}")

            time.sleep(5)

            # Step 2: Add parties
            if party_list:
                add_response = self.party_ops.post_parties(contract_type, contract_idx, party_list)
                if "error" in add_response:
                    self.fail(f"Failed to add parties from {filename}: {add_response}")
                log_info(self.logger, f"Added parties to {contract_type}:{contract_idx} from {filename}")

            time.sleep(5)

            # Step 3: Add settlements
            if settlement_list:
                add_response = self.settlement_ops.post_settlements(contract_type, contract_idx, settlement_list)
                if "error" in add_response:
                    self.fail(f"Failed to add settlements from {filename}: {add_response}")
                log_info(self.logger, f"Added settlements to {contract_type}:{contract_idx} from {filename}")

            time.sleep(5)

            # Step 4: Add transactions
            if transaction_list:
                add_response = self.transaction_ops.post_transactions(contract_type, contract_idx, transaction_list)
                if "error" in add_response:
                    self.fail(f"Failed to add transactions from {filename}: {add_response}")
                log_info(self.logger, f"Added transactions to {contract_type}:{contract_idx} from {filename}")

            time.sleep(5)

            # Step 5: Add artifacts
            if artifact_urls:
                add_response = self.artifact_ops.post_artifacts(contract_type, contract_idx, artifact_urls)
                if "error" in add_response:
                    self.fail(f"Failed to add artifacts from {filename}: {add_response}")
                log_info(self.logger, f"Added artifacts to {contract_type}:{contract_idx} from {filename}")

    @staticmethod
    def _get_json_files(directory):
        """Retrieve all JSON files from a directory."""
        return [f for f in os.listdir(directory) if f.endswith(".json")]

    @staticmethod
    def _load_json(filepath):
        """Load JSON from a file."""
        with open(filepath, "r") as file:
            return json.load(file)