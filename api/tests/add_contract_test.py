import os
import json
import logging
from datetime import datetime

from django.test import TestCase
from rest_framework import status

from api.operations import ContractOperations, CsrfOperations
from api.secrets import SecretsManager
from api.config import ConfigManager
from api.utilities.logging import log_info, log_error

class AddContractTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.logger = logging.getLogger(__name__)
        cls.secrets_manager = SecretsManager()
        cls.config_manager = ConfigManager()

    def setUp(self):
        """Set up authentication headers and initialize contract operations."""
        self.current_date = datetime.now().replace(microsecond=0).isoformat()
        self.headers = {
            'Authorization': f'Api-Key {self.secrets_manager.get_master_key()}',
            'Content-Type': 'application/json'
        }
        self.base_url = self.config_manager.get_base_url()
        self.csrf_ops = CsrfOperations(self.headers, self.base_url)
        self.csrf_token = self.csrf_ops.get_csrf_token()
        self.contract_ops = ContractOperations(self.headers, self.base_url, self.csrf_token)

    def test_successful_contract_creation(self):
        """Test successfully creating contracts for each contract type."""
        self._run_contract_test('valid_contracts', should_succeed=True)

    def test_failed_contract_creation(self):
        """Test failed contract creation due to validation errors."""
        self._run_contract_test('invalid_contracts', should_succeed=False)

    def _run_contract_test(self, directory, should_succeed):
        """
        Generalized function to run contract creation tests.
        
        :param directory: Name of the directory containing test JSON files.
        :param should_succeed: Boolean indicating if the test should succeed or fail.
        """
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'add_contract', directory)
        filenames = self._get_json_files(fixtures_dir)
        log_info(self.logger, f"Executing contract creation tests from {directory}: {filenames}")

        for filename in filenames:
            log_info(self.logger, f"Processing file: {filename}")
            contract_payload = self._load_json(os.path.join(fixtures_dir, filename))

            contract_type = contract_payload.get("contract_type")
            contract_data = contract_payload.get("contract_data")

            if not contract_type or not contract_data:
                self.fail(f"Invalid test data in {filename}: 'contract_type' and 'contract_data' must be provided.")

            log_info(self.logger, f"Sending contract_type: {contract_type}, contract_data: {contract_data}")
            response = self.contract_ops.post_contract(contract_type, contract_data)
            log_info(self.logger, f"Response for {filename}: {response}")

            if should_succeed:
                self._assert_successful_contract_creation(response)
            else:
                self._assert_failed_contract_creation(response)

    def _assert_successful_contract_creation(self, response):
        """
        Assert that the contract was successfully created.
        Expected response:
        {
            "contract_idx": <int>
        }
        """
        if "contract_idx" not in response:
            self.fail(f"Expected 'contract_idx' in response but got: {response}")

        contract_idx = response["contract_idx"]
        self.assertIsInstance(contract_idx, int, f"Invalid contract index: {contract_idx}")
        self.assertGreaterEqual(contract_idx, 0, f"Contract index should be non-negative: {contract_idx}")

    def _assert_failed_contract_creation(self, response):
        """
        Assert that contract creation failed due to validation errors.
        Expected response:
        {
            "error": "<error_message>"
        }
        """
        if "error" not in response:
            self.fail(f"Expected 'error' in response but got: {response}")

        error_message = response["error"]
        self.assertIsInstance(error_message, str, f"Expected error message as string but got: {error_message}")
        self.assertTrue(error_message.strip(), "Error message should not be empty.")

    @staticmethod
    def _get_json_files(directory):
        """Retrieve all JSON files from a directory."""
        return [f for f in os.listdir(directory) if f.endswith('.json')]

    @staticmethod
    def _load_json(filepath):
        """Load JSON from a file."""
        with open(filepath, 'r') as file:
            return json.load(file)