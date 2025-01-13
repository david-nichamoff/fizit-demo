import os
import json
import logging
import time

from django.test import TestCase
from rest_framework import status

from api.managers import SecretsManager, ConfigManager
from api.operations import ContractOperations, ArtifactOperations, CsrfOperations

from api.utilities.logging import log_info, log_warning, log_error

class TestArtifacts(TestCase):

    @classmethod
    def setUpTestData(cls):
        """Set up class-level test data."""
        cls.secrets_manager = SecretsManager()
        cls.config_manager = ConfigManager()
        cls.keys = cls.secrets_manager.load_keys()
        cls.config = cls.config_manager.load_config()
        cls.headers = {
            'Authorization': f'Api-Key {cls.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }

        cls.csrf_ops = CsrfOperations(cls.headers, cls.config)
        cls.csrf_token = cls.csrf_ops.get_csrf_token()

        cls.contract_ops = ContractOperations(cls.headers, cls.config, cls.csrf_token)
        cls.artifact_ops = ArtifactOperations(cls.headers, cls.config, cls.csrf_token)

        cls.logger = logging.getLogger(__name__)

    def setUp(self):
        """Set up instance-level state."""
        self.artifact_fixture_path = os.path.join(
            os.path.dirname(__file__), 'fixtures', 'artifacts_test', 'artifact.json'
        )

    def test_artifacts(self):
        """Test the entire artifact lifecycle."""
        log_info(self.logger, "Starting artifact lifecycle tests...")
        try:
            # Load test data
            contract_data, artifact_urls = self._load_fixture_data()

            # Create contract
            contract_idx = self._create_contract(contract_data)

            # Add artifacts
            self._test_add_artifacts(contract_idx, artifact_urls)

            # Retrieve and validate artifacts
            self._test_get_artifacts(contract_idx, artifact_urls)

            # Delete artifacts and confirm deletion
            self._test_delete_artifacts(contract_idx)

            log_info(self.logger, f"Artifact lifecycle tests completed successfully for contract {contract_idx}")

        except Exception as e:
            log_error(self.logger, f"Artifact lifecycle test failed: {e}")
            raise

    def _load_fixture_data(self):
        """Load and validate test data from the artifact fixture."""
        log_info(self.logger, f"Loading fixture data from {self.artifact_fixture_path}...")
        try:
            with open(self.artifact_fixture_path, 'r') as file:
                data = json.load(file)
                contract_data = data['contract']
                artifact_urls = data['artifacts']
                log_info(self.logger, "Fixture data loaded successfully.")
                return contract_data, artifact_urls
        except (json.JSONDecodeError, KeyError) as e:
            log_error(self.logger, f"Error processing fixture file: {e}")
            raise

    def _create_contract(self, contract_data):
        """Create a contract and return its index."""
        log_info(self.logger, "Creating contract...")

        response = self.contract_ops.post_contract(contract_data)
        self.assertGreaterEqual(response.get("contract_idx", -1), 0)
        contract_idx = response.get("contract_idx")
        log_info(self.logger, f"Contract created successfully with index {contract_idx}")

        return contract_idx

    def _test_add_artifacts(self, contract_idx, artifact_urls):
        """Test adding artifacts to a contract."""
        log_info(self.logger, f"Adding artifacts to contract {contract_idx}...")
        response = self.artifact_ops.post_artifacts(contract_idx, artifact_urls)
        self.assertGreaterEqual(response.get("count", 0), 0)
        log_info(self.logger, f"Artifacts added successfully for contract {contract_idx}")

    def _test_get_artifacts(self, contract_idx, expected_artifact_urls):
        """Test retrieving artifacts and validate the retrieved data."""
        log_info(self.logger, f"Retrieving artifacts for contract {contract_idx}...")

        artifacts = self.artifact_ops.get_artifacts(contract_idx)
        self.assertEqual(len(artifacts), len(expected_artifact_urls), f"Expected {len(expected_artifact_urls)} artifacts, but found {len(artifacts)}.")

        retrieved_artifact_urls = [artifact['s3_object_key'].split('/')[-1] for artifact in artifacts]
        expected_artifact_filenames = [url.split('/')[-1] for url in expected_artifact_urls]

        self.assertListEqual(
            sorted(retrieved_artifact_urls),
            sorted(expected_artifact_filenames),
            "Retrieved artifacts do not match the added artifacts."
        )
        log_info(self.logger, f"Artifacts validated successfully for contract {contract_idx}")

    def _test_delete_artifacts(self, contract_idx):

        """Test deleting artifacts and confirm their removal."""
        log_info(self.logger, f"Deleting artifacts for contract {contract_idx}...")
        response = self.artifact_ops.delete_artifacts(contract_idx)
        log_info(self.logger, f"Delete artifact response: {response}")

        self.assertIsNone(response)
        log_info(self.logger, f"Artifacts deleted successfully for contract {contract_idx}")

        # Validate deletion
        self._validate_artifact_deletion(contract_idx)

    def _validate_artifact_deletion(self, contract_idx):
        """Validate that all artifacts have been deleted."""

        log_info(self.logger, f"Validating artifact deletion for contract {contract_idx}...")
        time.sleep(5)  # Allow time for deletion to process

        artifacts = self.artifact_ops.get_artifacts(contract_idx)
        self.assertEqual(len(artifacts), 0, f"Artifacts were not deleted for contract {contract_idx}.")
        log_info(self.logger, f"Artifact deletion validated successfully for contract {contract_idx}")