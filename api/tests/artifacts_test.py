import os
import json
import logging
import time

from django.test import TestCase
from rest_framework import status

from api.managers import SecretsManager, ConfigManager
from api.operations import ContractOperations, ArtifactOperations, CsrfOperations

class TestArtifacts(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        # Initialize managers and configurations
        self.secrets_manager = SecretsManager()
        self.config_manager = ConfigManager()
        self.keys = self.secrets_manager.load_keys()
        self.config = self.config_manager.load_config()

        self.headers = {
            'Authorization': f'Api-Key {self.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }

        self.contract_ops = ContractOperations(self.headers, self.config)
        self.artifact_ops = ArtifactOperations(self.headers, self.config)
        self.csrf_ops = CsrfOperations(self.headers, self.config)

        self.logger = logging.getLogger(__name__)

    def test_artifacts(self):
        contract_fixture = os.path.join(os.path.dirname(__file__), 'fixtures', 'artifacts_test', 'artifact.json')
        
        with open(contract_fixture, 'r') as file:
            try:
                data = json.load(file)
                contract_data = data['contract']
                artifact_urls = data['artifacts']
                
                # Load contract and check response status
                response = self.contract_ops.load_contract(contract_data)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Failed to create contract.")

                # Get contract index from the response
                contract_idx = response.json()
                self.assertIsNotNone(contract_idx, "Contract index is missing in response.")
                
                # Add artifacts
                self._test_add_artifacts(contract_idx, artifact_urls)

                # Get and confirm artifacts
                self._test_get_artifacts(contract_idx, artifact_urls)

                # Proceed to delete artifacts
                self._test_delete_artifacts(contract_idx)

                print(f"Test completed successfully for contract {contract_idx}")

            except json.JSONDecodeError as e:
                self.fail(f"Error decoding JSON from file: {contract_fixture}, Error: {str(e)}")
            except KeyError as e:
                self.fail(f"Missing key in JSON fixture: {contract_fixture}, Error: {str(e)}")

    def _test_add_artifacts(self, contract_idx, artifact_urls):
        csrf_token = self.csrf_ops.get_csrf_token()
        
        # Call the add_artifacts method
        self.logger.info(f"Calling add_artifacts with contract {contract_idx} and urls {artifact_urls}")
        response = self.artifact_ops.add_artifacts(contract_idx, artifact_urls, csrf_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, f"Failed to add artifacts to contract {contract_idx}.")
        self.logger.info(f"Successfully added artifacts for contract {contract_idx}")

    def _test_get_artifacts(self, contract_idx, expected_artifact_urls):
        # Retrieve artifacts and confirm they match what was added
        response = self.artifact_ops.get_artifacts(contract_idx)
        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed to retrieve artifacts for contract {contract_idx}")
        
        artifacts = response.json()
        self.assertEqual(len(artifacts), len(expected_artifact_urls), f"Expected {len(expected_artifact_urls)} artifacts, but found {len(artifacts)}")

        # Confirm the artifacts match the URLs that were added
        retrieved_artifact_urls = [artifact['s3_object_key'].split('/')[-1] for artifact in artifacts]
        expected_artifact_filenames = [url.split('/')[-1] for url in expected_artifact_urls]

        self.assertListEqual(
            sorted(retrieved_artifact_urls), 
            sorted(expected_artifact_filenames), 
            "Retrieved artifacts do not match the added artifacts"
        )

        self.logger.info(f"Successfully confirmed artifacts for contract {contract_idx}")

    def _test_delete_artifacts(self, contract_idx):
        csrf_token = self.csrf_ops.get_csrf_token()

        # Delete the artifacts
        response = self.artifact_ops.delete_artifacts(contract_idx, csrf_token)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, f"Failed to delete artifacts for contract {contract_idx}.")
        self.logger.info(f"Successfully deleted artifacts for contract {contract_idx}")

        print("Sleeping to ensure that artifacts have been deleted") 
        time.sleep(10)

        # Check that the artifacts have been deleted
        response = self.artifact_ops.get_artifacts(contract_idx)
        artifacts = response.json()
        self.assertEqual(len(artifacts), 0, f"Artifacts should be deleted for contract {contract_idx}.")
        self.logger.info(f"All artifacts deleted for contract {contract_idx}")