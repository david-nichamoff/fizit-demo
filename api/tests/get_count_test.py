import logging

from django.test import TestCase

from api.operations import ContractOperations, CsrfOperations
from api.secrets import SecretsManager
from api.config import ConfigManager

class GetCountTest(TestCase):
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

    def test_contract_count_increments_after_add(self):
        """Test that contract count increases after adding a contract."""
        contract_type = "advance"

        # Step 1: Get the initial contract count
        initial_response = self.contract_ops.get_count(contract_type)

        if "error" in initial_response:
            self.fail(f"Failed to retrieve initial contract count: {initial_response}")

        initial_count = initial_response["count"]
        self.assertIsInstance(initial_count, int, "Contract count should be an integer.")

        # Step 2: Add a contract
        contract_data = {
            "extended_data": {"Contract #": initial_count + 1},
            "contract_name": "Test Contract",
            "funding_instr": {"bank": "mercury"},
            "transact_logic": {"*": [{"var": "barrels"}, {"var": "price"}]},
            "min_threshold_amt": "0.00",
            "max_threshold_amt": "1000000.00",
            "notes": "Valid test contract",
            "is_active": True,
            "is_quote": False
        }

        add_response = self.contract_ops.post_contract(contract_type, contract_data)

        if "error" in add_response:
            self.fail(f"Contract creation failed: {add_response}")

        self.assertIn("contract_idx", add_response, "Response should contain 'contract_idx'.")
        self.assertIsInstance(add_response["contract_idx"], int, "contract_idx should be an integer.")

        # Step 3: Get the contract count after adding
        final_response = self.contract_ops.get_count(contract_type)

        if "error" in final_response:
            self.fail(f"Failed to retrieve contract count after adding: {final_response}")

        final_count = final_response["count"]
        self.assertEqual(final_count, initial_count + 1, "Contract count should increment by 1 after adding a contract.")