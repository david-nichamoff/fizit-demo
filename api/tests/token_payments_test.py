import os
import json
import time
import logging
from decimal import Decimal

from django.test import TestCase
from rest_framework import status

from api.managers import SecretsManager, ConfigManager
from api.operations import (
    ContractOperations, PartyOperations, SettlementOperations,
    TransactionOperations, CsrfOperations, BankOperations
)

from api.utilities.logging import log_info, log_warning, log_error

class PayTokenTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.logger = logging.getLogger(__name__)

        """Initialize shared data for all test cases."""
        cls.secrets_manager = SecretsManager()
        cls.config_manager = ConfigManager()

        cls.keys = cls.secrets_manager.load_keys()
        cls.config = cls.config_manager.load_config()

    def setUp(self):
        """Set up resources for each test."""
        self.headers = {
            'Authorization': f'Api-Key {self.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }
        self.csrf_ops = CsrfOperations(self.headers, self.config)
        self.csrf_token = self.csrf_ops.get_csrf_token()

        self.payment_ops = BankOperations(self.headers, self.config, self.csrf_token)
        self.contract_ops = ContractOperations(self.headers, self.config, self.csrf_token)
        self.party_ops = PartyOperations(self.headers, self.config, self.csrf_token)
        self.settlement_ops = SettlementOperations(self.headers, self.config, self.csrf_token)
        self.transaction_ops = TransactionOperations(self.headers, self.config, self.csrf_token)

    def test_token_payments(self):
        """Test the full token payment workflow using fixture data."""
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'token_payments_test')
        advance_fixture = 'pay_advance.json'

        try:
            data = self._load_fixture(os.path.join(fixtures_dir, advance_fixture))
            contract_idx = self._create_contract(data['contract'])
            self._load_entities(contract_idx, data)
            self._validate_advances(contract_idx, data['contract'])
            self._validate_deposits(contract_idx, fixtures_dir)
            self._validate_residuals(contract_idx, data['contract'])
            self._compare_settlement_values(contract_idx)
        except (json.JSONDecodeError, KeyError) as e:
            self.fail(f"Error processing fixture data: {e}")

    def _create_contract(self, contract_data):
        """Create a contract and return its ID."""
        contract = self.contract_ops.post_contract(contract_data)
        contract_idx = contract.get("contract_idx", -1)
        self.assertGreater(contract_idx, -1)
        log_info(self.logger, f"Successfully created contract: {contract_idx}")
        return contract_idx

    def _load_entities(self, contract_idx, data):
        """Load related entities (parties, settlements, transactions) for a contract."""
        self._load_parties(contract_idx, data.get('parties', []))
        self._load_settlements(contract_idx, data.get('settlements', []))
        self._load_transactions(contract_idx, data.get('transactions', []))

    def _load_parties(self, contract_idx, parties_data):
        """Load parties into a contract."""
        response = self.party_ops.post_parties(contract_idx, parties_data) 
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Parties successfully loaded for contract: {contract_idx}")

    def _load_settlements(self, contract_idx, settlements_data):
        """Load settlements into a contract."""
        response = self.settlement_ops.post_settlements(contract_idx, settlements_data)
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Settlements successfully loaded for contract: {contract_idx}")

    def _load_transactions(self, contract_idx, transactions_data):
        """Load transactions into a contract."""
        response = self.transaction_ops.post_transactions(contract_idx, transactions_data)
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Transactions successfully loaded for contract: {contract_idx}")

    def _validate_advances(self, contract_idx, contract_data):
        """Validate and process advances for a contract."""
        advances = self._fetch_advances(contract_idx)
        self.assertEqual(len(advances), contract_data['extended_data'].get('advance_count', 0),
                         f"Unexpected advance count for contract {contract_idx}.")

        response = self.payment_ops.post_advances(contract_idx, advances)
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Advances successfully processed for contract: {contract_idx}")

        self._wait_and_validate_cleared_advances(contract_idx)

    def _fetch_advances(self, contract_idx):
        """Fetch advances for a contract."""
        advances = self.payment_ops.get_advances(contract_idx)
        return advances

    def _wait_and_validate_cleared_advances(self, contract_idx):
        """Wait and validate that advances are cleared."""
        time.sleep(10)  # Simulate processing delay
        advances = self._fetch_advances(contract_idx)
        self.assertEqual(len(advances), 0, f"Advances not cleared for contract {contract_idx}.")

    def _validate_deposits(self, contract_idx, fixtures_dir):
        """Validate deposits for a contract."""
        deposit_fixture = 'deposit_params.json'
        data = self._load_fixture(os.path.join(fixtures_dir, deposit_fixture))
        deposits = self.payment_ops.get_deposits(contract_idx, data['params']['start_date'], data['params']['end_date'])
        self.assertGreater(len(deposits), 0)

        # Validate expected deposit matches
        expected = data['deposits']
        match_found = any(
            Decimal(deposit['deposit_amt']) == Decimal(expected['deposit_amt'])
            and deposit['deposit_dt'] == expected['deposit_dt']
            for deposit in deposits
        )

        self.assertTrue(match_found, f"No matching deposit found for contract {contract_idx}.")
        log_info(self.logger, f"Deposits successfully validated for contract: {contract_idx}")

        # Now, call the payment_ops.add_deposits function with the deposits 
        add_deposit_response = self.payment_ops.post_deposit(contract_idx, expected)
        self.assertEqual(add_deposit_response["count"], 1)
        log_info(self.logger, f"Deposit successfully posted for contract: {contract_idx}")

    def _validate_residuals(self, contract_idx, contract_data):
        """Validate and process residuals for a contract."""
        residuals = self._fetch_residuals(contract_idx)
        self.assertEqual(len(residuals), contract_data['extended_data'].get('residual_count', 0),
                         f"Unexpected residual count for contract {contract_idx}.")

        response = self.payment_ops.post_residuals(contract_idx, residuals)
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"{response["count"]} residuals successfully processed for contract: {contract_idx}")

        self._wait_and_validate_cleared_residuals(contract_idx)

    def _fetch_residuals(self, contract_idx):
        """Fetch residuals for a contract."""
        residuals = self.payment_ops.get_residuals(contract_idx)
        return residuals

    def _wait_and_validate_cleared_residuals(self, contract_idx):
        """Wait and validate that residuals are cleared."""
        time.sleep(10)  # Simulate processing delay
        residuals = self._fetch_residuals(contract_idx)
        self.assertEqual(len(residuals), 0, f"Residuals not cleared for contract {contract_idx}.")
        log_info(self.logger, f"{residuals} cleared for contract {contract_idx}")

    def _compare_settlement_values(self, contract_idx):
        """Compare settlement values with contract data."""
        settlements = self.settlement_ops.get_settlements(contract_idx)
        self.assertGreater(len(settlements), 0)
        settlement = settlements[0] if settlements else None
        self.assertIsNotNone(settlement, f"No settlements found for contract {contract_idx}.")

        contract = self.contract_ops.get_contract(contract_idx)
        self._compare_field(settlement, contract, 'late_fee_amt')
        self._compare_field(settlement, contract, 'dispute_amt')
        self._compare_field(settlement, contract, 'residual_calc_amt', 'residual_pay_amt')

    def _compare_field(self, settlement, contract, contract_field, settlement_field=None):
        """Compare individual fields between settlement and contract."""
        settlement_field = settlement_field or contract_field
        self.assertEqual(
            settlement.get(settlement_field), contract['extended_data'].get(contract_field),
            f"Mismatch for field {settlement_field} in contract {contract['contract_idx']}."
        )

    def _load_fixture(self, path):
        """Load a JSON fixture."""
        with open(path, 'r') as file:
            return json.load(file)