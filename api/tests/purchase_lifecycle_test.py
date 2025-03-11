import os
import json
import logging
import time

from django.test import TestCase
from api.operations import (
    ContractOperations, PartyOperations, 
    TransactionOperations, ArtifactOperations, EventOperations, CsrfOperations
)
from api.secrets import SecretsManager
from api.config import ConfigManager
from api.utilities.logging import log_info, log_error


class PurchaseLifecycleTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Load contract fixture data."""
        cls.logger = logging.getLogger(__name__)
        cls.secrets_manager = SecretsManager()
        cls.config_manager = ConfigManager()

        contract_file = os.path.join(os.path.dirname(__file__), 'fixtures', 'purchase_fiat.json')

        try:
            with open(contract_file, 'r') as file:
                cls.contract_data = json.load(file)
            log_info(cls.logger, "Purchase contract test data loaded successfully.")
        except FileNotFoundError as e:
            log_error(cls.logger, f"Purchase contract test data file not found: {e}")
            raise
        except json.JSONDecodeError as e:
            log_error(cls.logger, f"Error decoding purchase contract JSON data: {e}")
            raise

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
        self.party_ops = PartyOperations(self.headers, self.base_url, self.csrf_token)
        self.transaction_ops = TransactionOperations(self.headers, self.base_url, self.csrf_token)
        self.artifact_ops = ArtifactOperations(self.headers, self.base_url, self.csrf_token)
        self.event_ops = EventOperations(self.headers, self.base_url, self.csrf_token)

        self.contract_type = self.contract_data["contract_type"]

    def test_contract_lifecycle(self):
        """Test the entire contract lifecycle."""
        contract_body = self.contract_data["contract"]

        # Store initial values
        service_fee_pct = float(contract_body["service_fee_pct"])
        service_fee_amt = float(contract_body["service_fee_amt"])

        # Step 1: Create the contract
        log_info(self.logger, f"Creating {self.contract_type} contract {contract_body}")
        create_response = self.contract_ops.post_contract(self.contract_type, contract_body)
        self.assertIn("contract_idx", create_response, "Response must contain 'contract_idx'")

        contract_idx = create_response["contract_idx"]
        self.assertIsInstance(contract_idx, int, "Contract index must be an integer.")

        log_info(self.logger, f"Contract {self.contract_type}:{contract_idx} created.")

        # Step 2: Validate contract creation events
        self._validate_event(contract_idx, "ContractAdded")

        # Step 3: Add parties
        parties = self.contract_data["parties"]
        log_info(self.logger, f"Adding {parties} to contract {contract_idx}")
        self.party_ops.post_parties(self.contract_type, contract_idx, parties)
        self._validate_event(contract_idx, "PartyAdded")

        # Step 4: Add settlements
        # Purchase contract do not have settlements so not included

        # Step 5: Add transactions
        transactions = self.contract_data["transactions"]
        log_info(self.logger, f"Adding {transactions} to contract {contract_idx}")
        self.transaction_ops.post_transactions(self.contract_type, contract_idx, transactions)
        self._validate_event(contract_idx, "TransactionAdded")

        # Step 6: Add artifacts
        artifacts = self.contract_data["artifacts"]
        log_info(self.logger, f"Adding artifacts to contract {contract_idx}...")
        self.artifact_ops.post_artifacts(self.contract_type, contract_idx, artifacts)
        self._validate_event(contract_idx, "ArtifactAdded")

        # Step 7: Retrieve and validate counts
        self._validate_counts(contract_idx, len(parties), len(artifacts))

        # Step 8: Retrieve transactions and calculate totals
        transactions_data = self.transaction_ops.get_transactions(self.contract_type, contract_idx)
        total_transact_amt = self._validate_transactions(
            transactions_data, service_fee_pct, service_fee_amt
        )

        # Step 9: Retrieve settlements and validate calculations
        # Settlements are not a part of purchase contract so skipping

        # Step 10: Update contract notes
        update_data = {"notes": "Updated by Unit Test"}
        self.contract_ops.patch_contract(self.contract_type, contract_idx, update_data)
        self._validate_event(contract_idx, "ContractUpdated")

        # Step 11: Retrieve contract and confirm update
        contract_response = self.contract_ops.get_contract(self.contract_type, contract_idx)
        self.assertEqual(contract_response["notes"], "Updated by Unit Test", "Contract note update failed.")

        # Step 12: Delete artifacts, transactions, settlements, parties
        self._delete_and_validate(contract_idx, "ArtifactsDeleted", self.artifact_ops.delete_artifacts)
        self._delete_and_validate(contract_idx, "TransactionsDeleted", self.transaction_ops.delete_transactions)
        self._delete_and_validate(contract_idx, "PartiesDeleted", self.party_ops.delete_parties)

        # Step 13: Validate that all components are deleted
        self._validate_empty(contract_idx)

    def _validate_event(self, contract_idx, event_type):
        """Check for an event with retries, filtering by contract_type, contract_idx, and to_addr."""
        retries = 5
        to_addr = self.config_manager.get_contract_address("purchase")

        for attempt in range(retries):
            events = self.event_ops.get_events(contract_type="purchase", contract_idx=contract_idx, to_addr=to_addr)
            event_found = any(e["event_type"] == event_type for e in events)

            if event_found:
                log_info(self.logger, f"Validated {event_type} for contract {contract_idx}.")
                return

            log_info(self.logger, f"Retrying event check for {event_type} (attempt {attempt+1}/{retries})...")
            time.sleep(3)

        self.fail(f"{event_type} event not found for contract {contract_idx}")

    def _validate_counts(self, contract_idx, expected_parties, expected_artifacts):
        """Validate counts of retrieved elements."""
        self.assertEqual(len(self.party_ops.get_parties(self.contract_type, contract_idx)), expected_parties)
        self.assertEqual(len(self.artifact_ops.get_artifacts(self.contract_type, contract_idx)), expected_artifacts)

    def _validate_transactions(self, transactions, service_fee_pct, service_fee_amt):
        """Validate transactions and compute totals."""
        total_transact_amt = 0

        for txn in transactions:
            transact_amt = float(txn["transact_amt"])

            total_transact_amt += transact_amt

        return total_transact_amt

    def _delete_and_validate(self, contract_idx, event_type, delete_func):
        """Delete an entity and confirm event generation."""
        delete_func(self.contract_type, contract_idx)
        self._validate_event(contract_idx, event_type)

    def _validate_empty(self, contract_idx):
        """Confirm all components are deleted."""
        self.assertEqual(len(self.artifact_ops.get_artifacts(self.contract_type, contract_idx)), 0)
        self.assertEqual(len(self.transaction_ops.get_transactions(self.contract_type, contract_idx)), 0)
        self.assertEqual(len(self.party_ops.get_parties(self.contract_type, contract_idx)), 0)