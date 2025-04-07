import os
import json
import logging
from django.test import TestCase

from api.operations import ContractOperations, CsrfOperations
from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_info, log_error

class AdvanceValidationTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Load contract fixture data.
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'advance_fiat.json')

        try:
            with open(fixture_path, 'r') as file:
                cls.valid_contract_data = json.load(file)
        except FileNotFoundError as e:
            raise
        except json.JSONDecodeError as e:
            raise

    def setUp(self):
        self.context = build_app_context()
        self.logger = logging.getLogger(__name__)

        self.headers = {
            'Authorization': f'Api-Key {self.context.secrets_manager.get_master_key()}',
            'Content-Type': 'application/json'
        }
        self.base_url = self.context.config_manager.get_base_url()
        self.csrf_ops = CsrfOperations(self.headers, self.base_url)
        self.csrf_token = self.csrf_ops.get_csrf_token()
        self.contract_ops = ContractOperations(self.headers, self.base_url, self.csrf_token)

    def test_invalid_contract_data(self):
        # Test contract creation with various invalid inputs.
        invalid_cases = [
            {
                "description": "Missing contract_name",
                "modifications": {"contract_name": ""},
            },
            {
                "description": "Invalid service_fee_pct",
                "modifications": {"service_fee_pct": "1.2000"},  # Greater than 1
            },
            #{
            #    "description": "Invalid transaction format",
            #    "modifications": {"transactions": [{"transact_dt": "invalid_date"}]},
            #},
            #{
            #    "description": "Settlement date issue",
            #    "modifications": {"settlements": [{"settle_due_dt": "2023-01-01T00:00:00", "transact_max_dt": "2024-02-01T00:00:00"}]},
            #},
            #{
            #    "description": "Invalid artifact URL",
            #    "modifications": {"artifacts": ["not_a_valid_url"]},
            #},
        ]

        for case in invalid_cases:
            with self.subTest(case=case["description"]):
                invalid_contract = self._modify_contract(self.valid_contract_data, case["modifications"])
                response = self.contract_ops.post_contract(invalid_contract["contract_type"], invalid_contract["contract"])
                
                log_info(self.logger, f"Test Case: {case['description']}")
                log_info(self.logger, f"Response: {response}")

                self.assertIn("error", response, f"Expected an error for case: {case['description']}")

    def _modify_contract(self, contract, modifications):
        # Return a copy of the contract with modifications applied.
        modified_contract = json.loads(json.dumps(contract))  # Deep copy
        for key, value in modifications.items():
            if key in modified_contract["contract"]:
                modified_contract["contract"][key] = value
            elif key in modified_contract:
                modified_contract[key] = value
        return modified_contract