import os
import json
import logging
from datetime import datetime

from django.test import TestCase
from rest_framework import status

from api.operations import ContractOperations, PartyOperations, SettlementOperations
from api.operations import TransactionOperations, CsrfOperations
from api.managers import SecretsManager, ConfigManager

from api.utilities.logging import log_info, log_warning, log_error

class IntegrityTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.logger = logging.getLogger(__name__)
        cls.secrets_manager = SecretsManager()
        cls.config_manager = ConfigManager()
        cls.keys = cls.secrets_manager.load_keys()
        cls.config = cls.config_manager.load_config()

    def setUp(self):
        self.current_date = datetime.now().replace(microsecond=0).isoformat()
        self.headers = {
            'Authorization': f'Api-Key {self.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }
        self.csrf_ops = CsrfOperations(self.headers, self.config)
        self.csrf_token = self.csrf_ops.get_csrf_token()

        self.contract_ops = ContractOperations(self.headers, self.config, self.csrf_token)
        self.party_ops = PartyOperations(self.headers, self.config, self.csrf_token)
        self.settlement_ops = SettlementOperations(self.headers, self.config, self.csrf_token)
        self.transaction_ops = TransactionOperations(self.headers, self.config, self.csrf_token)
        
    def test_contract_integrity(self):
        self._run_integrity_test(
            'contract_errors', 
            self._run_contract_integrity, 
            "contract", 
            "Invalid contract data."
        )

    def test_party_integrity(self):
        self._run_integrity_test(
            'party_errors', 
            self._run_party_integrity, 
            "parties", 
            "Invalid party data."
        )

    def test_settlement_integrity(self):
        self._run_integrity_test(
            'settlement_errors', 
            self._run_settlement_integrity, 
            "settlements", 
            "Invalid settlement data."
        )

    def test_transaction_integrity(self):
        self._run_integrity_test(
            'transaction_errors', 
            self._run_transaction_integrity, 
            "transactions", 
            "Invalid transaction data."
        )

    def _run_integrity_test(self, directory, test_method, key, error_message):
        """Generalized test runner for integrity tests."""
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'data_integrity_test', directory)
        filenames = self._get_json_files(fixtures_dir) 
        log_info(self.logger, f"Executing the following tests for {key}: {filenames}")

        for filename in filenames:
            log_info(self.logger, f"Processing file: {filename}")
            data = self._load_json(os.path.join(fixtures_dir, filename))

            try:
                # contract is prerequisite for settlements, transactions, parties
                if key != "contract":
                    response = self.contract_ops.post_contract(data["contract"])
                    log_info(self.logger, f"Response for {filename}: {response}")

                    contract_idx = response["contract_idx"]
                    self.assertGreaterEqual(contract_idx, 0)
                    log_info(self.logger, f"Added contract {contract_idx}")

                    test_method(contract_idx, data.get(key, []), error_message)
                else:
                    test_method(data.get(key, []), error_message)

            except KeyError as e:
                self.fail(f'Missing key in JSON from file: {filename}, Error: {str(e)}')
            except json.JSONDecodeError as e:
                self.fail(f'Error decoding JSON from file: {filename}, Error: {str(e)}')

    def _run_contract_integrity(self, contract_data, error_message):
        response = self.contract_ops.post_contract(contract_data)
        log_info(self.logger, f"Checking response {response} for contract")
        self._assert_bad_request(response, error_message)

    def _run_party_integrity(self, contract_idx, parties_data, error_message):
        response = self.party_ops.post_parties(contract_idx, parties_data)
        log_info(self.logger, f"Checking response {response} for parties")
        self._assert_bad_request(response, error_message)

    def _run_settlement_integrity(self, contract_idx, settlements_data, error_message):
        response = self.settlement_ops.post_settlements(contract_idx, settlements_data)
        log_info(self.logger, f"Checking response {response} for settlements")
        self._assert_bad_request(response, error_message)

    def _run_transaction_integrity(self, contract_idx, transactions_data, error_message):
        response = self.transaction_ops.post_transactions(contract_idx, transactions_data)
        log_info(self.logger, f"Checking response {response} for transactions")
        self._assert_bad_request(response, error_message)

    def _assert_bad_request(self, response, error_message):
        if "error" not in response:
            self.fail(f"{error_message} Expected 400 Bad Request but got {response.status_code}.\nResponse: {response.text}")

    @staticmethod
    def _get_json_files(directory):
        """Retrieve all JSON files from a directory."""
        return [f for f in os.listdir(directory) if f.endswith('.json')]

    @staticmethod
    def _load_json(filepath):
        """Load JSON from a file."""
        with open(filepath, 'r') as file:
            return json.load(file)