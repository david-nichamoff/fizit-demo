import os
import json
import logging

from datetime import datetime
from decimal import Decimal, ROUND_DOWN

from django.test import TestCase
from rest_framework import status

from api.operations import (
    ContractOperations, PartyOperations, SettlementOperations, 
    TransactionOperations, CsrfOperations
)
from api.managers import SecretsManager, ConfigManager

from api.utilities.logging import log_info, log_warning, log_error

class TransactionAmountTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        """Set up shared test data."""

    def setUp(self):
        """Set up resources for each test."""
        self.logger = logging.getLogger(__name__)
        self.secrets_manager = SecretsManager()
        self.config_manager = ConfigManager()

        self.keys = self.secrets_manager.load_keys()
        self.config = self.config_manager.load_config()

        self.headers = {
            'Authorization': f'Api-Key {self.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json',
        }
        self.csrf_ops = CsrfOperations(self.headers, self.config)
        self.csrf_token = self.csrf_ops.get_csrf_token()

        self.contract_ops = ContractOperations(self.headers, self.config, self.csrf_token)
        self.party_ops = PartyOperations(self.headers, self.config, self.csrf_token)
        self.settlement_ops = SettlementOperations(self.headers, self.config, self.csrf_token)
        self.transaction_ops = TransactionOperations(self.headers, self.config, self.csrf_token)

    def test_transactions(self):
        """Test transaction and settlement amount validations using fixture data."""
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'transact_amount_test')
        for filename in os.listdir(fixtures_dir):
            if filename.endswith('.json'):
                try:
                    data = self._load_fixture(os.path.join(fixtures_dir, filename))
                    log_info(self.logger, f"Processing fixture file: {filename}")
                    self._process_fixture_data(data)
                except (json.JSONDecodeError, KeyError) as e:
                    self.fail(f"Error processing file {filename}: {e}")

    def _process_fixture_data(self, data):
        """Process a single fixture for transactions and settlements."""
        contract_idx = self._create_contract(data['contract'])
        self._load_entities(contract_idx, data)
        self._validate_settlements(contract_idx)
        self._validate_transactions(contract_idx)

    def _create_contract(self, contract_data):
        """Create a contract and return its ID."""
        contract = self.contract_ops.post_contract(contract_data)
        self.assertGreaterEqual(contract["contract_idx"], 0)
        contract_idx = contract["contract_idx"]
        log_info(self.logger, f"Successfully created contract: {contract_idx}")
        return contract_idx

    def _load_entities(self, contract_idx, data):
        """Load related entities for a contract."""
        self._load_parties(contract_idx, data.get('parties', []))
        self._load_settlements(contract_idx, data.get('settlements', []))
        self._load_transactions(contract_idx, data.get('transactions', []))

    def _load_parties(self, contract_idx, parties_data):
        """Load parties into the contract."""
        parties = self.party_ops.post_parties(contract_idx, parties_data)
        log_info(self.logger, f"Successfully added {parties} to contract {contract_idx}")

    def _load_settlements(self, contract_idx, settlements_data):
        """Load settlements into the contract."""
        settlements = self.settlement_ops.post_settlements(contract_idx, settlements_data)
        log_info(self.logger, f"Successfully added {settlements} to contract {contract_idx}")

    def _load_transactions(self, contract_idx, transactions_data):
        """Load transactions into the contract."""
        transactions = self.transaction_ops.post_transactions(contract_idx, transactions_data)
        log_info(self.logger, f"Successfully added {transactions} to contract {contract_idx}")

    def _validate_settlements(self, contract_idx):
        """Validate settlement amounts."""
        settlements = self.settlement_ops.get_settlements(contract_idx)

        for settlement in settlements:
            self._validate_settlement_fields(settlement)

    def _validate_transactions(self, contract_idx):
        """Validate transaction amounts."""
        transactions = self.transaction_ops.get_transactions(contract_idx)

        for transaction in transactions:
            self._validate_transaction_fields(transaction)

    def _validate_settlement_fields(self, settlement):
        """Validate individual fields in a settlement."""
        expected_values = settlement.get("extended_data", {})
        self._assert_decimal_field(settlement, expected_values, "transact_count", is_int=True)
        self._assert_decimal_field(settlement, expected_values, "settle_exp_amt")
        self._assert_decimal_field(settlement, expected_values, "residual_exp_amt")
        log_info(self.logger, f"Settlement {settlement['settle_idx']} validation passed.")

    def _validate_transaction_fields(self, transaction):
        """Validate individual fields in a transaction."""
        expected_values = transaction.get("extended_data", {})
        self._assert_decimal_field(transaction, expected_values, "advance_amt")
        self._assert_decimal_field(transaction, expected_values, "service_fee_amt")
        log_info(self.logger, f"Transaction {transaction['transact_idx']} validation passed.")

    def _assert_decimal_field(self, obj, expected_values, field, is_int=False):
        """Assert that a field matches its expected value."""
        actual = Decimal(obj.get(field, 0))
        expected = Decimal(expected_values.get(field, 0))

        if is_int:
            self.assertEqual(
                int(actual), int(expected),
                f"Field '{field}' mismatch: expected {expected}, got {actual}."
            )
        else:
            self.assertEqual(
                actual.quantize(Decimal('0.01'), rounding=ROUND_DOWN),
                expected.quantize(Decimal('0.01'), rounding=ROUND_DOWN),
                f"Field '{field}' mismatch: expected {expected}, got {actual}."
            )

    def _load_fixture(self, path):
        """Load a JSON fixture."""
        with open(path, 'r') as file:
            return json.load(file)

    def _assert_status(self, response, expected_status, message):
        """Assert that a response has the expected status code."""
        self.assertEqual(response.status_code, expected_status, message)