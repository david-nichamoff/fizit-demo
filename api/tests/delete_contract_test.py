import os
import json
import logging
import time

from django.test import TestCase

from api.operations import ContractOperations, CsrfOperations
from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_info, log_error

class DeleteContractTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

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

    def test_soft_delete_contracts(self):
        """Test soft deletion of multiple contracts (is_active should switch to False)."""
        fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        filenames = ["advance_fiat.json", "purchase_fiat.json", "sale_fiat.json"]
        log_info(self.logger, f"Testing contract deletion for files: {filenames}")

        contract_records = []

        # Step 1: Create contracts and store contract_idx
        for filename in filenames:
            file_path = os.path.join(fixtures_dir, filename)
            contract_data = self._load_json(file_path)

            contract_type = contract_data["contract_type"]
            contract_body = contract_data["contract"]
            contract_body['contract_name'] = 'Delete Contract Test'

            create_response = self.contract_ops.post_contract(contract_type, contract_body)

            if "error" in create_response:
                self.fail(f"Contract creation failed: {create_response}")

            self.assertIn("contract_idx", create_response, "Response must include 'contract_idx'")
            contract_idx = create_response["contract_idx"]
            self.assertIsInstance(contract_idx, int, "Contract index must be an integer.")

            contract_records.append((contract_type, contract_idx))
            log_info(self.logger, f"Created contract {contract_type}:{contract_idx}")

            time.sleep(self.context.config_manager.get_network_sleep_time())

        # Step 2: Delete each contract
        for contract_type, contract_idx in contract_records:
            delete_response = self.contract_ops.delete_contract(contract_type, contract_idx)
            log_info(self.logger, f"Response for delete of {contract_type}:{contract_idx}: {delete_response}")

            if delete_response:
                self.fail(f"Contract deletion failed for {contract_type}:{contract_idx} - {delete_response}")

            log_info(self.logger, f"Deleted contract {contract_type}:{contract_idx}")

        # Step 3: Retrieve each contract and verify `is_active = False`
        for contract_type, contract_idx in contract_records:
            get_response = self.contract_ops.get_contract(contract_type, contract_idx)
            log_info(self.logger, f"Response from delete test: {get_response}")

            if "error" in get_response:
                self.fail(f"Contract retrieval failed after deletion for {contract_type}:{contract_idx} - {get_response}")

            self.assertFalse(
                get_response.get("is_active", True),
                f"Contract {contract_idx} should have 'is_active' set to False after deletion."
            )

            log_info(self.logger, f"Verified contract {contract_type}:{contract_idx} is marked inactive.")

    @staticmethod
    def _get_json_files(directory):
        """Retrieve all JSON files from a directory."""
        return [f for f in os.listdir(directory) if f.endswith(".json")]

    @staticmethod
    def _load_json(filepath):
        """Load JSON from a file."""
        with open(filepath, "r") as file:
            return json.load(file)