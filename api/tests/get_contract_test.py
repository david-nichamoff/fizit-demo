import os
import json
import logging
from django.test import TestCase

from api.operations import ContractOperations, CsrfOperations
from api.secrets import SecretsManager
from api.config import ConfigManager
from api.utilities.logging import log_info, log_error

class GetContractTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.logger = logging.getLogger(__name__)
        cls.secrets_manager = SecretsManager()
        cls.config_manager = ConfigManager()

    def setUp(self):
        self.headers = {
            'Authorization': f'Api-Key {self.secrets_manager.get_master_key()}',
            'Content-Type': 'application/json'
        }
        self.base_url = self.config_manager.get_base_url()
        self.csrf_ops = CsrfOperations(self.headers, self.base_url)
        self.csrf_token = self.csrf_ops.get_csrf_token()
        self.contract_ops = ContractOperations(self.headers, self.base_url, self.csrf_token)

    def test_get_contract(self):
        """Test retrieving contracts and verifying they match the loaded fixtures."""
        fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures", "get_contract")
        filenames = self._get_json_files(fixtures_dir)

        log_info(self.logger, f"Testing contract retrieval for files: {filenames}")

        for filename in filenames:
            file_path = os.path.join(fixtures_dir, filename)
            contract_data = self._load_json(file_path)

            contract_type = contract_data["contract_type"]
            contract_body = contract_data["contract_data"]

            # Step 1: Create contract and get contract_idx
            create_response = self.contract_ops.post_contract(contract_type, contract_body)

            if "error" in create_response:
                self.fail(f"Contract creation failed: {create_response}")

            self.assertIn("contract_idx", create_response, "Response must include 'contract_idx'")
            contract_idx = create_response["contract_idx"]
            self.assertIsInstance(contract_idx, int, "Contract index must be an integer.")

            log_info(self.logger, f"Created contract {contract_type}:{contract_idx}")

            # Step 2: Retrieve contract
            get_response = self.contract_ops.get_contract(contract_type, contract_idx)

            if "error" in get_response:
                self.fail(f"Failed to retrieve contract {contract_type}:{contract_idx} - {get_response}")

            # Step 3: Compare retrieved contract with expected contract data
            self._assert_contract_match(contract_body, get_response)

            log_info(self.logger, f"Verified contract {contract_type}:{contract_idx} matches expected data.")

    def _assert_contract_match(self, expected, actual):
        """
        Compare expected contract data with actual retrieved data.
        """
        ignored_fields = ["contract_idx"]  # Ignore fields that are dynamically generated

        for key, expected_value in expected.items():
            if key in ignored_fields:
                continue

            actual_value = actual.get(key)
            self.assertEqual(
                expected_value, actual_value,
                f"Mismatch in field '{key}'. Expected: {expected_value}, Got: {actual_value}"
            )

    @staticmethod
    def _get_json_files(directory):
        """Retrieve all JSON files from a directory."""
        return [f for f in os.listdir(directory) if f.endswith(".json")]

    @staticmethod
    def _load_json(filepath):
        """Load JSON from a file."""
        with open(filepath, "r") as file:
            return json.load(file)