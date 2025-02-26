import os
import json
import logging
from django.test import TestCase
from rest_framework import status

from api.operations import ContractOperations, CsrfOperations
from api.secrets import SecretsManager
from api.config import ConfigManager
from api.utilities.logging import log_info, log_error


class AdvanceValidationTest(TestCase):
    pass

    """
    @classmethod
    def setUpTestData(cls):
        # Load contract fixture data.
        cls.logger = logging.getLogger(__name__)
        cls.secrets_manager = SecretsManager()
        cls.config_manager = ConfigManager()

        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'advance_fiat.json')

        try:
            with open(fixture_path, 'r') as file:
                cls.valid_contract_data = json.load(file)
            log_info(cls.logger, "Validation test data loaded successfully.")
        except FileNotFoundError as e:
            log_error(cls.logger, f"Test data file not found: {e}")
            raise
        except json.JSONDecodeError as e:
            log_error(cls.logger, f"Error decoding JSON data: {e}")
            raise

    def setUp(self):
        # Set up authentication headers and initialize contract operations.
        self.headers = {
            'Authorization': f'Api-Key {self.secrets_manager.get_master_key()}',
            'Content-Type': 'application/json'
        }
        self.base_url = self.config_manager.get_base_url()
        self.csrf_ops = CsrfOperations(self.headers, self.base_url)
        self.csrf_token = self.csrf_ops.get_csrf_token()
        self.contract_ops = ContractOperations(self.headers, self.base_url, self.csrf_token)

    def test_invalid_contract_data(self):
        # Test contract creation with various invalid inputs.
        invalid_cases = [
            {
                "description": "Missing contract_name",
                "modifications": {"contract_name": ""},
                "expected_error": "contract_name must not be empty"
            },
            {
                "description": "Invalid service_fee_pct",
                "modifications": {"service_fee_pct": "1.2000"},  # Greater than 1
                "expected_error": "service_fee_pct must be between 0.0000 and 1.0000"
            },
            {
                "description": "Negative min_threshold_amt",
                "modifications": {"min_threshold_amt": "-10.00"},
                "expected_error": "min_threshold_amt must be a positive amount"
            },
            {
                "description": "Invalid transaction format",
                "modifications": {"transactions": [{"transact_dt": "invalid_date"}]},
                "expected_error": "transact_dt must be a valid datetime"
            },
            {
                "description": "Settlement date issue",
                "modifications": {"settlements": [{"settle_due_dt": "2023-01-01T00:00:00", "transact_max_dt": "2024-02-01T00:00:00"}]},
                "expected_error": "settle_due_dt must be after transact_max_dt"
            },
            {
                "description": "Invalid artifact URL",
                "modifications": {"artifacts": ["not_a_valid_url"]},
                "expected_error": "artifacts must contain valid URLs"
            },
        ]

        for case in invalid_cases:
            with self.subTest(case=case["description"]):
                invalid_contract = self._modify_contract(self.valid_contract_data, case["modifications"])
                response = self.contract_ops.post_contract(invalid_contract["contract_type"], invalid_contract["contract"])
                
                log_info(self.logger, f"Test Case: {case['description']}")
                log_info(self.logger, f"Response: {response}")

                self.assertIn("error", response, f"Expected an error for case: {case['description']}")
                self.assertIn(case["expected_error"], response["error"], f"Unexpected error message: {response['error']}")

    def _modify_contract(self, contract, modifications):
        # Return a copy of the contract with modifications applied.
        modified_contract = json.loads(json.dumps(contract))  # Deep copy
        for key, value in modifications.items():
            if key in modified_contract["contract"]:
                modified_contract["contract"][key] = value
            elif key in modified_contract:
                modified_contract[key] = value
        return modified_contract
    """