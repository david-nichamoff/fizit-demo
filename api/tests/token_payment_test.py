import os
import json
import time
import logging
from decimal import Decimal

from django.test import TestCase
from api.models.event_model import Event  # Import Event model
from rest_framework import status

from api.secrets import SecretsManager
from api.config import ConfigManager
from api.operations import (
    ContractOperations, PartyOperations, SettlementOperations,
    TransactionOperations, CsrfOperations, BankOperations, EventOperations
)

from api.utilities.logging import log_info, log_warning, log_error


class PayTokenTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.logger = logging.getLogger(__name__)

        """Initialize shared data for all test cases."""
        cls.secrets_manager = SecretsManager()
        cls.config_manager = ConfigManager()

    def setUp(self):
        """Set up resources for each test."""
        self.headers = {
            'Authorization': f'Api-Key {self.secrets_manager.get_master_key()}',
            'Content-Type': 'application/json'
        }
        self.csrf_ops = CsrfOperations(self.headers, self.config_manager.get_base_url())
        self.csrf_token = self.csrf_ops.get_csrf_token()

        self.payment_ops = BankOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.contract_ops = ContractOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.party_ops = PartyOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.settlement_ops = SettlementOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.transaction_ops = TransactionOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.event_ops = EventOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)

    def test_token_payments(self):
        """Test the full token payment workflow using fixture data."""
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'token_payment')
        advance_fixture = 'pay_advance.json'

        try:
            data = self._load_fixture(os.path.join(fixtures_dir, advance_fixture))
            contract_type = data["contract_type"]
            contract_idx = self._create_contract(contract_type, data['contract'])
            self._load_entities(contract_type, contract_idx, data)
            self._validate_advances(contract_type, contract_idx, data['contract'])
            self._validate_deposits(contract_type, contract_idx, fixtures_dir)
            self._validate_residuals(contract_type, contract_idx, data['contract'])
            self._compare_settlement_values(contract_type, contract_idx)
        except (json.JSONDecodeError, KeyError) as e:
            self.fail(f"Error processing fixture data: {e}")

    def _create_contract(self, contract_type, contract_data):
        """Create a contract and return its ID."""
        contract = self.contract_ops.post_contract(contract_type, contract_data)
        contract_idx = contract.get("contract_idx", -1)
        self.assertGreater(contract_idx, -1)
        log_info(self.logger, f"Successfully created contract: {contract_idx}")
        return contract_idx

    def _load_entities(self, contract_type, contract_idx, data):
        """Load related entities (parties, settlements, transactions) for a contract."""
        self._load_parties(contract_type, contract_idx, data.get('parties', []))
        self._load_settlements(contract_type, contract_idx, data.get('settlements', []))
        self._load_transactions(contract_type, contract_idx, data.get('transactions', []))

    def _load_parties(self, contract_type, contract_idx, parties_data):
        """Load parties into a contract."""
        response = self.party_ops.post_parties(contract_type, contract_idx, parties_data)
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Parties successfully loaded for contract: {contract_idx}")

    def _load_settlements(self, contract_type, contract_idx, settlements_data):
        """Load settlements into a contract."""
        response = self.settlement_ops.post_settlements(contract_type, contract_idx, settlements_data)
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Settlements successfully loaded for contract: {contract_idx}")

    def _load_transactions(self, contract_type, contract_idx, transactions_data):
        """Load transactions into a contract."""
        response = self.transaction_ops.post_transactions(contract_type, contract_idx, transactions_data)
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Transactions successfully loaded for contract: {contract_idx}")

    def _validate_advances(self, contract_type, contract_idx, contract_data):
        """Validate and process advances for a contract."""
        advances = self._fetch_advances(contract_type, contract_idx)
        expected_advance_count = contract_data["extended_data"].get("advance_count", 0)

        self.assertEqual(len(advances), expected_advance_count,
                         f"Unexpected advance count for contract {contract_idx}.")

        response = self.payment_ops.post_advances(contract_type, contract_idx, advances)
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Advances successfully response {response} processed for contract: {contract_idx}")

        self._validate_event_log("PayAdvance", contract_type, contract_idx)
        self._wait_and_validate_cleared_advances(contract_type, contract_idx)

    def _fetch_advances(self, contract_type, contract_idx):
        """Fetch advances for a contract."""
        return self.payment_ops.get_advances(contract_type, contract_idx)

    def _wait_and_validate_cleared_advances(self, contract_type, contract_idx):
        """Wait and validate that advances are cleared."""
        time.sleep(10)  # Simulate processing delay
        advances = self._fetch_advances(contract_type, contract_idx)
        self.assertEqual(len(advances), 0, f"Advances not cleared for contract {contract_idx}.")

    def _validate_deposits(self, contract_type, contract_idx, fixtures_dir):
        """Validate deposits for a contract."""
        deposit_fixture = 'deposit_params.json'
        data = self._load_fixture(os.path.join(fixtures_dir, deposit_fixture))
        deposits = self.payment_ops.get_deposits(contract_type, contract_idx, data['params']['start_date'], data['params']['end_date'])
        self.assertGreater(len(deposits), 0)

        expected = data['deposits']
        match_found = any(
            Decimal(deposit['deposit_amt']) == Decimal(expected['deposit_amt'])
            and deposit['deposit_dt'] == expected['deposit_dt']
            for deposit in deposits
        )

        self.assertTrue(match_found, f"No matching deposit found for contract {contract_idx}.")
        log_info(self.logger, f"Deposits successfully validated for contract: {contract_idx}")

        add_deposit_response = self.payment_ops.post_deposit(contract_type, contract_idx, expected)
        self.assertEqual(add_deposit_response["count"], 1)
        log_info(self.logger, f"Deposit successfully posted for contract: {contract_idx}")

    def _validate_residuals(self, contract_type, contract_idx, contract_data):
        """Validate and process residuals for a contract."""
        residuals = self._fetch_residuals(contract_type, contract_idx)
        expected_residual_count = contract_data["extended_data"].get("residual_count", 0)

        self.assertEqual(len(residuals), expected_residual_count,
                         f"Unexpected residual count for contract {contract_idx}.")

        response = self.payment_ops.post_residuals(contract_type, contract_idx, residuals)
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Residuals successfully processed for contract: {contract_idx}")

        self._validate_event_log("ResidualPaid", contract_type, contract_idx)
        self._wait_and_validate_cleared_residuals(contract_type, contract_idx)

    def _fetch_residuals(self, contract_type, contract_idx):
        """Fetch residuals for a contract."""
        return self.payment_ops.get_residuals(contract_type, contract_idx)

    def _wait_and_validate_cleared_residuals(self, contract_type, contract_idx):
        """Wait and validate that residuals are cleared."""
        time.sleep(10)
        residuals = self._fetch_residuals(contract_type, contract_idx)
        self.assertEqual(len(residuals), 0, f"Residuals not cleared for contract {contract_idx}.")
                         
    def _compare_settlement_values(self, contract_type, contract_idx):
        """Compare settlement values with contract data."""
        settlements = self.settlement_ops.get_settlements(contract_type, contract_idx)
        contract = self.contract_ops.get_contract(contract_type, contract_idx)

        log_info(self.logger, f"Settlements: {settlements}")
        log_info(self.logger, f"Contract: {contract}")

        for field in ['late_fee_amt', 'dispute_amt', 'residual_calc_amt']:
            self.assertEqual(
                settlements[0].get(field),
                contract['extended_data'].get(field),
                f"Mismatch for field {field} in contract {contract_idx}."
            )

    def _compare_settlement_values(self, contract_type, contract_idx):
        """Compare settlement values with contract data."""
        settlements = self.settlement_ops.get_settlements(contract_type, contract_idx)
        contract = self.contract_ops.get_contract(contract_type, contract_idx)

        log_info(self.logger, f"Settlements: {settlements}")
        log_info(self.logger, f"Contract: {contract}")

        for field in ['late_fee_amt', 'dispute_amt', 'residual_calc_amt']:
            self.assertEqual(
                settlements[0].get(field),
                contract['extended_data'].get(field),
                f"Mismatch for field {field} in contract {contract_idx}."
            )

    def _validate_event_log(self, event_type, contract_type, contract_idx):
        """Wait up to 20 seconds for an event to appear in the API."""
        log_info(self.logger, f"Validating event for {contract_type}:{contract_idx}")

        event = None
        for attempt in range(20):  # Try for 20 seconds
            events = self.event_ops.get_events(contract_type=contract_type, contract_idx=contract_idx)
            log_info(self.logger, f"Events: {events}")

            if events:
                event = next((e for e in events if e["event_type"] == event_type), None)
                if event:
                    break

            log_warning(self.logger, f"Waiting for event {event_type} (attempt {attempt + 1}/20)...")
            time.sleep(1)

        self.assertIsNotNone(event, f"Event {event_type} not found for contract {contract_idx}")
        self.assertEqual(event["status"], "complete", f"Event status incorrect: {event['status']}")
        log_info(self.logger, f"Event validated: {event}")

    def _load_fixture(self, path):
        """Load a JSON fixture."""
        with open(path, 'r') as file:
            return json.load(file)