import os
import json
import logging
import time

from django.test import TestCase

from api.operations import ContractOperations, ArtifactOperations, CsrfOperations
from api.secrets import SecretsManager
from api.config import ConfigManager
from api.utilities.logging import log_info, log_error


class ArtifactTest(TestCase):
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
        self.artifact_ops = ArtifactOperations(self.headers, self.base_url, self.csrf_token)

    def test_artifact_operations(self):
        """Test artifact lifecycle: create contract, add artifacts, retrieve, and delete."""
        fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures", "artifact")
        filenames = self._get_json_files(fixtures_dir)

        if not filenames:
            self.fail("No test files found in fixtures/artifact")

        for filename in filenames:
            file_path = os.path.join(fixtures_dir, filename)
            contract_data = self._load_json(file_path)

            contract_type = contract_data["contract_type"]
            contract_body = contract_data["contract_data"]
            artifact_list = contract_data["artifacts"]

            # Step 1: Create contract
            create_response = self.contract_ops.post_contract(contract_type, contract_body)

            if "error" in create_response:
                self.fail(f"Failed to create contract from {filename}: {create_response}")

            self.assertIn("contract_idx", create_response, "Response must contain 'contract_idx'")
            contract_idx = create_response["contract_idx"]
            self.assertIsInstance(contract_idx, int, "Contract index must be an integer")

            log_info(self.logger, f"Created contract {contract_type}:{contract_idx} from {filename}")

            time.sleep(5)

            # Step 2: Add artifacts
            add_response = self.artifact_ops.post_artifacts(contract_type, contract_idx, artifact_list)

            if "error" in add_response:
                self.fail(f"Failed to add artifacts from {filename}: {add_response}")

            log_info(self.logger, f"Added {artifact_list} to {contract_type}:{contract_idx} from {filename}")

            time.sleep(5)

            # Step 3: Retrieve artifacts and validate
            retrieved_artifacts = self.artifact_ops.get_artifacts(contract_type, contract_idx)
            log_info(self.logger, f"Retrieved artifacts from {contract_type}:{contract_idx}: {retrieved_artifacts}")

            if "error" in retrieved_artifacts:
                self.fail(f"Failed to retrieve artifacts from {filename}: {retrieved_artifacts}")

            self.assertEqual(len(retrieved_artifacts), len(artifact_list), f"Mismatch in artifact count for {filename}")

            retrieved_artifact_urls = [artifact['s3_object_key'].split('/')[-1] for artifact in retrieved_artifacts]
            expected_artifact_filenames = [url.split('/')[-1] for url in artifact_list]

            self.assertListEqual(
                sorted(retrieved_artifact_urls),
                sorted(expected_artifact_filenames),
                "Retrieved artifacts do not match the added artifacts."
            )

            log_info(self.logger, f"Retrieved artifacts match expected values for {contract_type}:{contract_idx} from {filename}")

            # Step 4: Delete artifacts
            delete_response = self.artifact_ops.delete_artifacts(contract_type, contract_idx)

            if delete_response:
                self.fail(f"Failed to delete artifacts from {filename}: {delete_response}")

            log_info(self.logger, f"Deleted artifacts from {contract_type}:{contract_idx} from {filename}")

            time.sleep(5)

            # Step 5: Verify deletion
            get_response_after_delete = self.artifact_ops.get_artifacts(contract_type, contract_idx)

            if "error" in get_response_after_delete:
                self.fail(f"Failed to retrieve artifacts after deletion for {filename}: {get_response_after_delete}")

            self.assertEqual(len(get_response_after_delete), 0, f"Artifacts should be empty after deletion for {filename}")

            log_info(self.logger, f"Verified artifacts were deleted for {contract_type}:{contract_idx} from {filename}")

    @staticmethod
    def _get_json_files(directory):
        """Retrieve all JSON files from a directory."""
        return [f for f in os.listdir(directory) if f.endswith(".json")]

    @staticmethod
    def _load_json(filepath):
        """Load JSON from a file."""
        with open(filepath, "r") as file:
            return json.load(file)