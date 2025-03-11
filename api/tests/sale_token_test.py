import os
import json
import time
import logging
from decimal import Decimal

from django.test import TestCase

from api.secrets import SecretsManager
from api.config import ConfigManager
from api.operations import (
    ContractOperations, PartyOperations, SettlementOperations,
    TransactionOperations, CsrfOperations, BankOperations, EventOperations
)

from api.utilities.logging import log_info, log_warning, log_error


class SaleTokenTest(TestCase):

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
        self.csrf_ops = CsrfOperations(self.headers, self.config_manager.get_base_url())
        self.csrf_token = self.csrf_ops.get_csrf_token()

        self.payment_ops = BankOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.contract_ops = ContractOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.party_ops = PartyOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.settlement_ops = SettlementOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.transaction_ops = TransactionOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.event_ops = EventOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)

    def test_token_payments(self):
        """Test full lifecycle for token-based payments."""
        fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "sale_token.json")

        try:
            data = self._load_fixture(fixture_path)
            contract_type = data["contract_type"]
            contract_idx = self._create_contract(contract_type, data['contract'])
            self._load_entities(contract_type, contract_idx, data)
            self._process_deposits(contract_type, contract_idx, data["params"], data["deposits"])
            self._process_distributions(contract_type, contract_idx)

        except (json.JSONDecodeError, KeyError) as e:
            self.fail(f"Error processing fixture data: {e}")

    def _create_contract(self, contract_type, contract_data):
        """Create a contract and return contract index."""
        contract_data['contract_name'] = 'Sale Token Test'
        response = self.contract_ops.post_contract(contract_type, contract_data)
        contract_idx = response.get("contract_idx", -1)
        self.assertGreater(contract_idx, -1)
        log_info(self.logger, f"Contract created: {contract_idx}")
        return contract_idx

    def _load_entities(self, contract_type, contract_idx, data):
        """Load contract entities (parties, settlements, transactions)."""
        self._load_parties(contract_type, contract_idx, data.get('parties', []))
        self._load_settlements(contract_type, contract_idx, data.get('settlements', []))
        self._load_transactions(contract_type, contract_idx, data.get('transactions', []))

    def _load_parties(self, contract_type, contract_idx, parties_data):
        """Load parties for the contract."""
        response = self.party_ops.post_parties(contract_type, contract_idx, parties_data)
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Parties loaded for contract {contract_idx}")

    def _load_settlements(self, contract_type, contract_idx, settlements_data):
        """Load settlements for the contract."""
        response = self.settlement_ops.post_settlements(contract_type, contract_idx, settlements_data)
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Settlements loaded for contract {contract_idx}")

    def _load_transactions(self, contract_type, contract_idx, transactions_data):
        """Load transactions for the contract."""
        response = self.transaction_ops.post_transactions(contract_type, contract_idx, transactions_data)
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Transactions loaded for contract {contract_idx}")

    def _process_deposits(self, contract_type, contract_idx, deposit_params, expected_deposit):
        """Retrieve and validate token deposits."""
        start_date, end_date = deposit_params["start_date"], deposit_params["end_date"]

        deposits = self.payment_ops.get_deposits(contract_type, contract_idx, start_date, end_date)
        self.assertGreater(len(deposits), 0, f"No deposits found for contract {contract_idx}")

        matched_deposit = next(
            (d for d in deposits if
                d["tx_hash"] == expected_deposit["tx_hash"] and
                Decimal(d["deposit_amt"]) == Decimal(expected_deposit["deposit_amt"])
            ),
            None
        )

        self.assertIsNotNone(matched_deposit, f"Expected deposit not found for contract {contract_idx}")

        response = self.payment_ops.post_deposit(contract_type, contract_idx, expected_deposit)
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Deposit processed: {response}")

        from_addr = self.config_manager.get_wallet_address("Transactor")
        to_addr = self.config_manager.get_contract_address("sale")
        self._validate_event_log("PostSettlement", contract_type, contract_idx, from_addr=from_addr, to_addr=to_addr)

    def _process_distributions(self, contract_type, contract_idx):
        """Retrieve and process distributions"""
        distributions = self.payment_ops.get_distributions(contract_type, contract_idx)
        self.assertGreater(len(distributions), 0, f"No distributions found for contract {contract_idx}")

        response = self.payment_ops.post_distributions(contract_type, contract_idx, distributions)
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Distributions processed: {response}")

        from_addr = self.config_manager.get_wallet_address("Transactor")
        to_addr = self.config_manager.get_contract_address("sale")
        self._validate_event_log("DistributionPaid", contract_type, contract_idx, from_addr=from_addr, to_addr=to_addr)

        # from_addr = self.config_manager.get_party_address("FIZIT")
        # self._validate_event_log("ERC-20 Transfer", contract_type, contract_idx, from_addr=from_addr)

    def _validate_event_log(self, event_type, contract_type, contract_idx, from_addr=None, to_addr=None):
        """Wait up to 30 seconds for an event to appear with status 'complete'."""
        log_info(self.logger, f"Validating event {event_type} for contract {contract_idx}")

        event = None
        max_attempts = 5  # Increase retries to 5
        wait_time = 10  # Wait 10 seconds between attempts

        for attempt in range(max_attempts):
            events = self.event_ops.get_events(
                contract_type=contract_type, contract_idx=contract_idx, 
                from_addr=from_addr, to_addr=to_addr
            )

            event = next((e for e in events if e["event_type"] == event_type), None)

            if event:
                if event["status"] == "complete":
                    log_info(self.logger, f"Event validated: {event}")
                    break  # Exit loop only when status is "complete"
                else:
                    log_warning(self.logger, f"Event {event_type} found but still pending (attempt {attempt + 1}/{max_attempts})...")

            else:
                log_warning(self.logger, f"Waiting for event {event_type} (attempt {attempt + 1}/{max_attempts})...")

            time.sleep(wait_time)  # Wait before retrying

        self.assertIsNotNone(event, f"Event {event_type} not found for contract {contract_idx}")
        self.assertEqual(event["status"], "complete", f"Event status incorrect: {event['status']}")
        log_info(self.logger, f"Event validated: {event}")

    def _load_fixture(self, path):
        """Load a JSON fixture."""
        with open(path, 'r') as file:
            return json.load(file)