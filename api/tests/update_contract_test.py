import os
import json
import logging
from django.test import TestCase

from api.operations import ContractOperations, CsrfOperations
from api.secrets import SecretsManager
from api.config import ConfigManager
from api.utilities.logging import log_info, log_error


class UpdateContractTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.logger = logging.getLogger(__name__)
        cls.secrets_manager = SecretsManager()
        cls.config_manager = ConfigManager()

    def setUp(self):
        """Set up authentication headers and initialize contract operations."""
        self.headers = {
            'Authorization': f'Api-Key {self.secrets_manager.get_master_key()}',
            'Content-Type': 'application/json'
        }
        self.base_url = self.config_manager.get_base_url()
        self.csrf_ops = CsrfOperations(self.headers, self.base_url)
        self.csrf_token = self.csrf_ops.get_csrf_token()
        self.contract_ops = ContractOperations(self.headers, self.base_url, self.csrf_token)

    def test_successful_contract_update(self):
        """Test updating an existing contract with valid data."""
        self._run_update_test('valid_updates', should_succeed=True)

    def test_failed_contract_update(self):
        """Test updating a contract with invalid data."""
        self._run_update_test('invalid_updates', should_succeed=False)

    def _run_update_test(self, directory, should_succeed):
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'update_contract', directory)
        filenames = self._get_json_files(fixtures_dir)

        for filename in filenames:
            contract_data = self._load_json(os.path.join(fixtures_dir, filename))
            contract_type = contract_data["contract_type"]
            contract_body = contract_data["contract_data"]
            update_data = contract_data["update_data"]

            # Step 1: Create the contract
            create_response = self.contract_ops.post_contract(contract_type, contract_body)

            if "error" in create_response:
                self.fail(f"Contract creation failed: {create_response}")

            self.assertIn("contract_idx", create_response, "Response must include 'contract_idx'")
            contract_idx = create_response["contract_idx"]
            self.assertIsInstance(contract_idx, int, "Contract index must be an integer.")

            log_info(self.logger, f"Created contract {contract_type}:{contract_idx}")

            # Step 2: Update the contract
            log_info(self.logger, f"Updating contract {contract_type}:{contract_idx} with data: {update_data}")
            response = self.contract_ops.patch_contract(contract_type, contract_idx, update_data)
            log_info(self.logger, f"Response from update: {response}")

            if should_succeed:
                self._assert_successful_contract_update(response)
            else:
                self._assert_failed_contract_update(response)

            # Step 3: Retrieve the contract and validate changes
            if should_succeed:
                self._validate_updated_contract(contract_type, contract_idx, update_data)

    def _assert_successful_contract_update(self, response):
        if "contract_idx" not in response or not isinstance(response["contract_idx"], int):
            self.fail(f"Expected successful contract update but got: {response}")

    def _assert_failed_contract_update(self, response):
        if "error" not in response:
            self.fail(f"Expected contract update failure but got: {response}")

    def _validate_updated_contract(self, contract_type, contract_idx, expected_data):
        """Retrieve the updated contract and verify its data."""
        response = self.contract_ops.get_contract(contract_type, contract_idx)

        if "error" in response:
            self.fail(f"Failed to retrieve updated contract: {response}")

        log_info(self.logger, f"Retrieved updated contract: {response}")
        log_info(self.logger, f"Expected updated data: {expected_data}")

        for key, expected_value in expected_data.items():
            self.assertEqual(
                response.get(key), expected_value,
                f"Mismatch for '{key}': Expected {expected_value}, Got {response.get(key)}"
            )

    @staticmethod
    def _get_json_files(directory):
        return [f for f in os.listdir(directory) if f.endswith('.json')]

    @staticmethod
    def _load_json(filepath):
        with open(filepath, 'r') as file:
            return json.load(file)