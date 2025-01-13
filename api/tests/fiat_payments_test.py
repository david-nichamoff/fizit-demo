import os
import json
import time
import logging
from datetime import datetime

from django.test import TestCase
from rest_framework import status

from api.managers import SecretsManager, ConfigManager
from api.operations import (
    ContractOperations, PartyOperations, SettlementOperations,
    TransactionOperations, CsrfOperations, BankOperations
)

from api.utilities.logging import log_info, log_warning, log_error

class PayFiatTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.logger = logging.getLogger(__name__)
        cls.secrets_manager = SecretsManager()
        cls.config_manager = ConfigManager()

        cls.keys = cls.secrets_manager.load_keys()
        cls.config = cls.config_manager.load_config()

    def setUp(self):
        self.headers = {
            'Authorization': f'Api-Key {self.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }
        self.current_date = datetime.now().replace(microsecond=0).isoformat()

        self.csrf_ops = CsrfOperations(self.headers, self.config)
        self.csrf_token = self.csrf_ops.get_csrf_token()

        # Initialize operations
        self.payment_ops = BankOperations(self.headers, self.config, self.csrf_token)
        self.contract_ops = ContractOperations(self.headers, self.config, self.csrf_token)
        self.party_ops = PartyOperations(self.headers, self.config, self.csrf_token)
        self.settlement_ops = SettlementOperations(self.headers, self.config, self.csrf_token)
        self.transaction_ops = TransactionOperations(self.headers, self.config, self.csrf_token)

    def test_payments(self):
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'fiat_payments_test')
        log_info(self.logger, "Starting payment tests...")

        self._run_fiat_payment_tests(
            advance_filename='pay_advance.json',
            deposit_filename='deposit_params.json',
            fixtures_dir=fixtures_dir
        )

    def _run_fiat_payment_tests(self, advance_filename, deposit_filename, fixtures_dir):
        try:
            contract_data = self._load_fixture(fixtures_dir, advance_filename)

            log_info(self.logger, f"Running tests for {advance_filename}")

            contract_idx = self._test_create_contract(contract_data['contract'])
            self._load_entities(contract_idx, contract_data)
            self._test_get_advances(contract_idx, contract_data['contract'])
            self._test_get_deposits(contract_idx, deposit_filename)
            self._test_get_residuals(contract_idx, contract_data['contract'])
            self._test_compare_settlement_values(contract_idx)

        except json.JSONDecodeError as e:
            self.fail(f"Error decoding JSON from {advance_filename}: {str(e)}")
        except KeyError as e:
            self.fail(f"Missing key in JSON from {advance_filename}: {str(e)}")

    def _load_entities(self, contract_idx, data):
        self._test_load_parties(contract_idx, data['parties'])
        self._test_load_settlements(contract_idx, data['settlements'])
        self._test_load_transactions(contract_idx, data['transactions'])

    def _test_create_contract(self, contract_data):
        response = self.contract_ops.post_contract(contract_data)
        contract_idx = response.get("contract_idx")
        self.assertGreater(contract_idx, 0)
        log_info(self.logger, f"Added contract: {contract_idx}")
        return contract_idx

    def _test_load_parties(self, contract_idx, parties_data):
        parties = self.party_ops.post_parties(contract_idx, parties_data)
        self.assertGreater(len(parties), 0)
        log_info(self.logger, f"Parties loaded for contract {contract_idx}")

    def _test_load_settlements(self, contract_idx, settlements_data):
        settlements = self.settlement_ops.post_settlements(contract_idx, settlements_data)
        self.assertGreater(len(settlements), 0)
        log_info(self.logger, f"Settlements loaded for contract {contract_idx}")

    def _test_load_transactions(self, contract_idx, transactions_data):
        transactions = self.transaction_ops.post_transactions(contract_idx, transactions_data)
        self.assertGreater(len(transactions), 0)
        log_info(self.logger, f"Transactions loaded for contract {contract_idx}")

    def _test_get_advances(self, contract_idx, contract_data):
        expected_advance_count = contract_data["extended_data"].get("advance_count")
        advances = self._get_data(self.payment_ops.get_advances, contract_idx, "advance amount")

        self.assertEqual(len(advances), expected_advance_count,
                         f"Expected {expected_advance_count} advances but got {len(advances)} for contract {contract_idx}.")

        log_info(self.logger, f"Advances loaded for contract {contract_idx}.")
        self._process_advances(contract_idx, advances)

    def _test_get_deposits(self, contract_idx, fixture_filename):
        data = self._load_fixture(os.path.dirname(__file__), os.path.join("fixtures" , "fiat_payments_test", fixture_filename))
        deposits = self._get_data(
            lambda idx: self.payment_ops.get_deposits(idx, data["params"]["start_date"], data["params"]["end_date"]),
            contract_idx, "deposits"
        )
        self._validate_and_add_deposits(contract_idx, deposits, data["deposits"])

    def _test_get_residuals(self, contract_idx, contract_data):
        expected_residual_count = contract_data["extended_data"].get("residual_count")
        residuals = self._get_data(self.payment_ops.get_residuals, contract_idx, "residual amounts")
        self.assertEqual(len(residuals), expected_residual_count,
                         f"Expected {expected_residual_count} residuals but got {len(residuals)} for contract {contract_idx}.")

        log_info(self.logger, f"Residuals loaded for contract {contract_idx}.")
        self._process_residuals(contract_idx, residuals)

    def _test_compare_settlement_values(self, contract_idx):
        log_info(self.logger, f"Validating settlement values for contract {contract_idx}...")
        settlement = self._get_data(self.settlement_ops.get_settlements, contract_idx, "settlements")[0]
        contract = self.contract_ops.get_contract(contract_idx)
        self._compare_values(settlement, contract, ['late_fee_amt', 'dispute_amt', 'residual_calc_amt', 'residual_pay_amt'])
        log_info(self.logger, f"Settlement values validated for contract {contract_idx}.")

    def _compare_values(self, settlement, contract, fields):
        for field in fields:
            expected = contract["extended_data"].get(field)
            actual = settlement.get(field)
            self.assertEqual(
                actual, expected,
                f"Expected {field} {expected} but got {actual} for contract."
            )

    def _get_data(self, operation, contract_idx, data_type):
        response = operation(contract_idx)
        log_info(self.logger, f"Get data for {data_type} returned {response}")
        self.assertGreater(len(response), 0)
        return response

    def _process_advances(self, contract_idx, advances):
        response = self.payment_ops.post_advances(contract_idx, advances)
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Advances processed for contract {contract_idx}. Waiting for processing...")
        time.sleep(10)

    def _process_residuals(self, contract_idx, residuals):
        response = self.payment_ops.post_residuals(contract_idx, residuals)
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Residuals processed for contract {contract_idx}. Waiting for processing...")
        time.sleep(10)

    def _validate_and_add_deposits(self, contract_idx, deposits, expected_deposit):

        log_info(self.logger, f"Matching deposits: {deposits} and expected_deposits {expected_deposit}")

        match_found = False
        for deposit in deposits:
            if (deposit["account_id"] == expected_deposit["account_id"] and 
                deposit["deposit_amt"] == expected_deposit["deposit_amt"]):
                match_found = True

        self.assertTrue(match_found, f"Expected deposit not found for contract {contract_idx}.")
        response = self.payment_ops.post_deposit(contract_idx, expected_deposit)
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Deposits added for contract {contract_idx}.")

    def _load_fixture(self, base_dir, filename):
        path = os.path.join(base_dir, filename)
        with open(path, 'r') as file:
            return json.load(file)