import os
import json
import logging
from django.test import TestCase
from rest_framework import status

from api.operations import (
    ContractOperations, PartyOperations, SettlementOperations, 
    TransactionOperations, CsrfOperations
)
from api.secrets import SecretsManager
from api.config import ConfigManager
from api.utilities.logging import log_info, log_warning, log_error

class AuthorizationTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        """Load authorization test data from fixture file."""
        contract_file = os.path.join(os.path.dirname(__file__), 'fixtures', 'authorization', 'authorization.json')
        cls.logger = logging.getLogger(__name__)

        try:
            with open(contract_file, 'r') as file:
                cls.contract_data = json.load(file)
            log_info(cls.logger, "Test data loaded successfully.")
        except FileNotFoundError as e:
            log_error(cls.logger, f"Test data file not found: {e}")
            raise
        except json.JSONDecodeError as e:
            log_error(cls.logger, f"Error decoding JSON data: {e}")
            raise

    def setUp(self):
        """Set up authentication headers, CSRF tokens, and contract operations."""
        log_info(self.logger, "Setting up test environment...")
        self.secrets_manager = SecretsManager()
        self.config_manager = ConfigManager()

        self.headers = {'Content-Type': 'application/json'}
        self.csrf_ops = CsrfOperations(self.headers, self.config_manager.get_base_url())
        self.csrf_token = self.csrf_ops.get_csrf_token()

        self.contract_ops = ContractOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.party_ops = PartyOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.settlement_ops = SettlementOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.transaction_ops = TransactionOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)

        log_info(self.logger, "Test environment setup complete.")

        self.contract_type = self.contract_data["contract_type"]

        self.scenarios = [
            {'key': None, "post_status": "Unauthorized", 'get_status': 'Unauthorized',
             "detail": 'Authorization header missing or empty'},
            {'key': 'XXXXXXX', 'post_status': "Unauthorized", 'get_status': 'Unauthorized',
             "detail": 'Invalid API key'},
            {'key': self.secrets_manager.get_partner_api_key("Affiliate"), 'post_status': "Unauthorized",
             'get_status': 'Authorized', "detail": 'You do not have permission to perform this action.'},
            {'key': self.secrets_manager.get_master_key(), 'post_status': "Authorized", 'get_status': 'Authorized',
             'message': f"FIZIT_MASTER_KEY should succeed."}
        ]

    def test_authorization_failures(self):
        """Run authorization tests for contracts, parties, settlements, and transactions."""
        try:
            log_info(self.logger, "Starting authorization tests...")
            contract_idx = self._test_contract_authorization()
            self._test_party_authorization(contract_idx)
            self._test_settlement_authorization(contract_idx)
            self._test_transaction_authorization(contract_idx)
            log_info(self.logger, "All authorization tests passed.")
        except AssertionError as e:
            log_error(self.logger, f"Authorization test failed: {e}")
            raise

    def _test_contract_authorization(self):
        """Test authorization for creating contracts."""
        log_info(self.logger, "Testing contract authorization...")
        contract_idx = None

        for scenario in self.scenarios:
            self._set_auth_header(scenario["key"])

            response = self._perform_operation(self.contract_ops.post_contract, self.contract_type, self.contract_data['contract'])
            log_info(self.logger, f"Contract scenario {scenario['key']} returned: {response}")

            if scenario["post_status"] == "Unauthorized":
                self.assertEqual(response.get("detail"), scenario["detail"], f"Unexpected response for key: {scenario['key']}")
            else:
                contract_idx = response.get("contract_idx")
                self.assertIsInstance(contract_idx, int, "Contract index must be an integer")
                self.assertGreaterEqual(contract_idx, 0)

        return contract_idx

    def _test_party_authorization(self, contract_idx):
        """Test authorization for party-related operations."""
        log_info(self.logger, "Testing party authorization...")
        self._test_authorization(self.party_ops.post_parties, contract_idx, self.contract_data['parties'], "Adding parties")
        self._test_authorization(self.party_ops.get_parties, contract_idx, None, "Retrieving parties")

    def _test_settlement_authorization(self, contract_idx):
        """Test authorization for settlement-related operations."""
        log_info(self.logger, "Testing settlement authorization...")
        self._test_authorization(self.settlement_ops.post_settlements, contract_idx, self.contract_data['settlements'], "Adding settlements")
        self._test_authorization(self.settlement_ops.get_settlements, contract_idx, None, "Retrieving settlements")

    def _test_transaction_authorization(self, contract_idx):
        """Test authorization for transaction-related operations."""
        log_info(self.logger, "Testing transaction authorization...")
        self._test_authorization(self.transaction_ops.post_transactions, contract_idx, self.contract_data['transactions'], "Adding transactions")
        self._test_authorization(self.transaction_ops.get_transactions, contract_idx, None, "Retrieving transactions")

    def _test_authorization(self, operation, contract_idx, data, operation_name):
        """Run authorization checks for a given operation."""
        for scenario in self.scenarios:
            self._set_auth_header(scenario['key'])

            if data is None:  # GET request
                response = self._perform_operation(operation, self.contract_type, contract_idx)
                log_info(self.logger, f"{operation_name} scenario {scenario['key']} returned: {response}")

                if scenario["get_status"] == "Unauthorized":
                    self.assertEqual(response.get("detail"), scenario["detail"], f"Unexpected response for key: {scenario['key']}")
                else:
                    self.assertGreaterEqual(len(response), 0, f"Unexpected empty response for key: {scenario['key']}")

            else:  # POST request
                response = self._perform_operation(operation, self.contract_type, contract_idx, data)
                log_info(self.logger, f"{operation_name} scenario {scenario['key']} returned: {response}")

                if scenario["post_status"] == "Unauthorized":
                    self.assertEqual(response.get("detail"), scenario["detail"], f"Unexpected response for key: {scenario['key']}")
                else:
                    self.assertGreaterEqual(response.get("count", 0), 0, f"Unexpected empty response for key: {scenario['key']}")

    def _perform_operation(self, operation, *args, **kwargs):
        """Perform a given operation and return the response."""
        return operation(*args, **kwargs)

    def _set_auth_header(self, api_key):
        """Set or remove the API key in the request headers."""
        if api_key:
            self.headers['Authorization'] = f"Api-Key {api_key}"
        else:
            self.headers.pop('Authorization', None)