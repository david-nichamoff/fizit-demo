import os
import json
import logging
import time

from django.test import TestCase

from api.operations import ContractOperations, PartyOperations, CsrfOperations
from api.secrets import SecretsManager
from api.config import ConfigManager
from api.utilities.logging import log_info, log_error

class PartyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.logger = logging.getLogger(__name__)
        cls.secrets_manager = SecretsManager()
        cls.config_manager = ConfigManager()

    def setUp(self):
        """Set up authentication headers and initialize operations."""
        self.headers = {
            'Authorization': f'Api-Key {self.secrets_manager.get_master_key()}',
            'Content-Type': 'application/json'
        }
        self.base_url = self.config_manager.get_base_url()
        self.csrf_ops = CsrfOperations(self.headers, self.base_url)
        self.csrf_token = self.csrf_ops.get_csrf_token()
        self.contract_ops = ContractOperations(self.headers, self.base_url, self.csrf_token)
        self.party_ops = PartyOperations(self.headers, self.base_url, self.csrf_token)

    def test_party_operations(self):
        """Test party lifecycle: create contract, add parties, retrieve, and delete."""
        fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        filenames = ["advance_fiat.json", "purchase_fiat.json", "sale_fiat.json"]

        if not filenames:
            self.fail("No test files found in fixtures/party")

        for filename in filenames:
            file_path = os.path.join(fixtures_dir, filename)
            contract_data = self._load_json(file_path)

            contract_type = contract_data["contract_type"]
            contract_body = contract_data["contract"]
            party_list = contract_data["parties"]

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
            add_response = self.party_ops.post_parties(contract_type, contract_idx, party_list)

            if "error" in add_response:
                self.fail(f"Failed to add parties from {filename}: {add_response}")

            log_info(self.logger, f"Added {party_list} to {contract_type}:{contract_idx} from {filename}")

            time.sleep(5)

            # Step 3: Retrieve parties and validate
            retrieved_parties = self.party_ops.get_parties(contract_type, contract_idx)
            log_info(self.logger, f"Retrieve parties from {contract_type}:{contract_idx}: {retrieved_parties}")

            if "error" in retrieved_parties:
                self.fail(f"Failed to retrieve parties from {filename}: {retrieved_parties}")

            self.assertEqual(len(retrieved_parties), len(party_list), f"Mismatch in party count for {filename}")

            for expected, actual in zip(party_list, retrieved_parties):
                self.assertEqual(expected["party_code"], actual["party_code"], f"Mismatch in party_code: {actual}")
                self.assertEqual(expected["party_type"], actual["party_type"], f"Mismatch in party_type: {actual}")

            log_info(self.logger, f"Retrieved parties match expected values for {contract_type}:{contract_idx} from {filename}")

            # Step 4: Delete parties
            delete_response = self.party_ops.delete_parties(contract_type, contract_idx)

            if delete_response:
                self.fail(f"Failed to delete parties from {filename}: {delete_response}")

            log_info(self.logger, f"Deleted parties from {contract_type}:{contract_idx} from {filename}")

            time.sleep(5)

            # Step 5: Verify deletion
            get_response_after_delete = self.party_ops.get_parties(contract_type, contract_idx)

            if "error" in get_response_after_delete:
                self.fail(f"Failed to retrieve parties after deletion for {filename}: {get_response_after_delete}")

            self.assertEqual(len(get_response_after_delete), 0, f"Parties should be empty after deletion for {filename}")

            log_info(self.logger, f"Verified parties were deleted for {contract_type}:{contract_idx} from {filename}")

    @staticmethod
    def _get_json_files(directory):
        """Retrieve all JSON files from a directory."""
        return [f for f in os.listdir(directory) if f.endswith(".json")]

    @staticmethod
    def _load_json(filepath):
        """Load JSON from a file."""
        with open(filepath, "r") as file:
            return json.load(file)