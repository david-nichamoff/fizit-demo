import os
import json
import logging
from django.test import TestCase
from django.utils.timezone import now

from api.operations import ContractOperations, EventOperations
from api.adapters.bank.token_adapter import TokenAdapter
from api.secrets import SecretsManager
from api.config import ConfigManager
from api.utilities.logging import log_info, log_error


class EventTests(TestCase):
    """Test event logging for contract creation and token transfers."""

    @classmethod
    def setUpTestData(cls):
        """Set up shared test data that is safe for pickling."""
        cls.logger = logging.getLogger(__name__)
        cls.config_manager = ConfigManager()
        cls.secrets_manager = SecretsManager()

        cls.headers = {
            'Authorization': f'Api-Key {cls.secrets_manager.get_master_key()}',
            'Content-Type': 'application/json'
        }

        cls.fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures", "event")

    def setUp(self):
        """Set up objects that should be created per test to avoid pickling issues."""
        self.contract_ops = ContractOperations(self.headers, self.config_manager.get_base_url())
        self.event_ops = EventOperations(self.headers, self.config_manager.get_base_url())
        self.token_adapter = TokenAdapter() 

    def test_contract_creation_logs_event(self):
        """Test that ContractAdded events are logged in the Event table for each contract type."""

        for fixture_name in ["advance_valid_event.json", "ticketing_valid_event.json"]:
            fixture_path = os.path.join(self.fixtures_dir, fixture_name)

            with open(fixture_path, "r") as file:
                data = json.load(file)

            contract_type = data["contract_type"]
            contract_data = data["contract_data"]

            log_info(self.logger, f"Creating contract: {contract_type}")

            # Create contract
            contract = self.contract_ops.post_contract(contract_type, contract_data)
            self.assertGreaterEqual(contract["contract_idx"], 0)

            contract_idx = contract["contract_idx"]
            log_info(self.logger, f"Successfully created contract {contract_type} with idx {contract_idx}")

            # Validate event logging
            events = self.event_ops.get_events(contract_type, contract_idx)
            self.assertGreater(len(events), 0, f"No events found for contract {contract_idx}")

            contract_added_event = next((e for e in events if e["event_type"] == "ContractAdded"), None)
            self.assertIsNotNone(contract_added_event, f"ContractAdded event missing for contract {contract_idx}")

            log_info(self.logger, f"ContractAdded event validated for {contract_type} (contract_idx: {contract_idx})")