import os
import json
import time
import logging
from datetime import datetime

from django.test import TestCase
from rest_framework import status

from api.secrets import SecretsManager
from api.config import ConfigManager
from api.registry import RegistryManager
from api.operations import (
    ContractOperations, PartyOperations, SettlementOperations,
    TransactionOperations, CsrfOperations, BankOperations
)

from api.utilities.logging import log_info, log_warning, log_error

class AdvanceFiatTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.logger = logging.getLogger(__name__)
        cls.secrets_manager = SecretsManager()
        cls.config_manager = ConfigManager()
        cls.registry_manager = RegistryManager()

    def setUp(self):
        self.headers = {
            'Authorization': f'Api-Key {self.secrets_manager.get_master_key()}',
            'Content-Type': 'application/json'
        }
        self.current_date = datetime.now().replace(microsecond=0).isoformat()

        self.csrf_ops = CsrfOperations(self.headers, self.config_manager.get_base_url())
        self.csrf_token = self.csrf_ops.get_csrf_token()

        # Initialize operations
        self.payment_ops = BankOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.contract_ops = ContractOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.party_ops = PartyOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.settlement_ops = SettlementOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)
        self.transaction_ops = TransactionOperations(self.headers, self.config_manager.get_base_url(), self.csrf_token)

    def test_payments(self):
        filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'advance_fiat.json')
        log_info(self.logger, "Starting payment tests...")

        with open(filename, 'r') as file:
            contract_data = json.load(file)

        try:
            contract_type = contract_data["contract_type"]
            contract_idx = self._test_create_contract(contract_type, contract_data['contract'])
            self._load_entities(contract_type, contract_idx, contract_data)

            self._test_get_advances(contract_type, contract_idx, contract_data['contract'])
            self._test_get_deposits(contract_type, contract_idx, contract_data["deposit_params"], contract_data["deposits"])
            self._process_residuals(contract_type, contract_idx)

        except json.JSONDecodeError as e:
            self.fail(f"Error decoding JSON from {filename}: {str(e)}")
        except KeyError as e:
            self.fail(f"Missing key in JSON from {filename}: {str(e)}")

    def _load_entities(self, contract_type, contract_idx, data):
        self._test_load_parties(contract_type, contract_idx, data['parties'])
        self._test_load_settlements(contract_type, contract_idx, data['settlements'])
        self._test_load_transactions(contract_type, contract_idx, data['transactions'])

    def _test_create_contract(self, contract_type, contract_data):
        contract_data["contract_name"] = "Advance Fiat Test"
        response = self.contract_ops.post_contract(contract_type, contract_data)
        contract_idx = response.get("contract_idx")
        self.assertGreater(contract_idx, 0)
        log_info(self.logger, f"Added contract: {contract_idx}")
        return contract_idx

    def _test_load_parties(self, contract_type, contract_idx, parties_data):
        response = self.party_ops.post_parties(contract_type, contract_idx, parties_data)
        log_info(self.logger, f"Response from load_parties: {response}")
        self.assertGreater(response['count'], 0)
        log_info(self.logger, f"Parties loaded for contract {contract_idx}")

    def _test_load_settlements(self, contract_type, contract_idx, settlements_data):
        response = self.settlement_ops.post_settlements(contract_type, contract_idx, settlements_data)
        log_info(self.logger, f"Response from load_settlements: {response}")
        self.assertGreater(response['count'], 0)
        log_info(self.logger, f"Settlements loaded for contract {contract_idx}")

    def _test_load_transactions(self, contract_type, contract_idx, transactions_data):
        response = self.transaction_ops.post_transactions(contract_type, contract_idx, transactions_data)
        log_info(self.logger, f"Response from load_transactions: {response}")
        self.assertGreater(response['count'], 0)
        log_info(self.logger, f"Transactions loaded for contract {contract_idx}")

    def _test_get_advances(self, contract_type, contract_idx, contract_data):
        advances = self.payment_ops.get_advances(contract_type, contract_idx)
        log_info(self.logger, f"Advances loaded for contract {contract_type}:{contract_idx}: {advances}")
        transactions = self.transaction_ops.get_transactions(contract_type, contract_idx)
        self.assertEqual(len(advances), len(transactions), f"Expected {len(transactions)} advances but got {len(advances)} for contract {contract_idx}.")
        
        # Process advances after retrieval
        self._process_advances(contract_type, contract_idx, advances)

    def _process_advances(self, contract_type, contract_idx, advances):
        """Process advances by posting them."""
        response = self.payment_ops.post_advances(contract_type, contract_idx, advances)
        log_info(self.logger, f"Response from process_advances: {response}")
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Advances processed for contract {contract_idx}. Waiting for processing...")
        time.sleep(10)

    def _test_get_deposits(self, contract_type, contract_idx, deposit_params, expected_deposit):
        """Retrieve deposits using start_date and end_date from deposit_params, then validate and post the deposit."""
        start_date = deposit_params["start_date"]
        end_date = deposit_params["end_date"]

        log_info(self.logger, f"Fetching deposits for contract {contract_idx} from {start_date} to {end_date}")
        
        deposits = self.payment_ops.get_deposits(contract_type, contract_idx, start_date, end_date)
        log_info(self.logger, f"Deposits loaded for contract {contract_idx}: {deposits}")

        # Convert expected deposit amount to float
        expected_deposit_amt = float(expected_deposit["deposit_amt"])

        # Match the retrieved deposit with the expected deposit
        matched_deposit = next(
            (d for d in deposits if 
                d["account_id"] == expected_deposit["account_id"] and 
                float(d["deposit_amt"]) == expected_deposit_amt and
                d["tx_hash"] == expected_deposit["tx_hash"] and
                d["counterparty"] == expected_deposit["counterparty"]
            ),
            None
        )

        log_info(self.logger, f"Comparing against expected deposit: {expected_deposit}")

        self.assertIsNotNone(matched_deposit, f"Expected deposit not found for contract {contract_idx}.")

        # Post the matched deposit
        response = self.payment_ops.post_deposit(contract_type, contract_idx, expected_deposit)
        log_info(self.logger, f"Response from post_deposit: {response}")
        self.assertGreater(response["count"], 0)
        log_info(self.logger, f"Deposits added for contract {contract_idx}.")

    def _process_residuals(self, contract_type, contract_idx):
        """Process residuals after deposits have been posted."""
        residuals = self.payment_ops.get_residuals(contract_type, contract_idx)
        log_info(self.logger, f"Residuals retrieved for processing: {residuals}")

        response = self.payment_ops.post_residuals(contract_type, contract_idx, residuals)
        log_info(self.logger, f"Response from post_residuals: {response}")
        self.assertGreater(response["count"], 0, f"Expected residuals to be processed but got {response}")
        log_info(self.logger, f"Residuals processed for contract {contract_idx}. Waiting for processing...")
