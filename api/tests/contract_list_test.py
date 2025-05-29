import os
import json
import logging

from django.test import TestCase

from api.operations import ContractOperations, PartyOperations, CsrfOperations
from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_debug, log_info, log_error, log_warning

class ContractListTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.context = build_app_context()
        cls.logger = logging.getLogger(__name__)

        # Load fixture
        fixture_path = os.path.join(os.path.dirname(__file__), "fixtures/contract_list.json")
        with open(fixture_path) as f:
            cls.contract_data = json.load(f)

        cls.MASTER_KEY = cls.context.secrets_manager.get_master_key()
        cls.base_url = cls.context.config_manager.get_base_url()

        cls.headers = {
            'Authorization': f'Api-Key {cls.MASTER_KEY}',
            'Content-Type': 'application/json'
        }

        cls.csrf_ops = CsrfOperations(cls.headers, cls.base_url)
        cls.csrf_token = cls.csrf_ops.get_csrf_token()
        cls.contract_ops = ContractOperations(cls.headers, cls.base_url, cls.csrf_token)
        cls.party_ops = PartyOperations(cls.headers, cls.base_url, cls.csrf_token)

        # Snapshot contract counts before loading
        cls.before_counts = {
            "fizit": len(cls.contract_ops.list_contracts_by_party_code("fizit")),
            "refiner": len(cls.contract_ops.list_contracts_by_party_code("refiner")),
            "supplier_1": len(cls.contract_ops.list_contracts_by_party_code("supplier_1")),
            "supplier_2": len(cls.contract_ops.list_contracts_by_party_code("supplier_2")),
        }

        # Add all contracts
        for contract_entry in cls.contract_data:
            log_info(cls.logger, f"Processing contract_entry {contract_entry}")
            contract = contract_entry["contract"]
            contract_type = contract_entry["contract_type"]

            contract_response = cls.contract_ops.post_contract(contract_type, contract)
            contract_idx = contract_response["contract_idx"]
            log_info(cls.logger, f"Created {contract_type} contract {contract_idx}")

            cls.party_ops.post_parties(contract_type, contract_idx, contract_entry["parties"])

        # Snapshot contract counts after loading
        cls.after_counts = {
            "fizit": len(cls.contract_ops.list_contracts_by_party_code("fizit")),
            "refiner": len(cls.contract_ops.list_contracts_by_party_code("refiner")),
            "supplier_1": len(cls.contract_ops.list_contracts_by_party_code("supplier_1")),
            "supplier_2": len(cls.contract_ops.list_contracts_by_party_code("supplier_2")),
        }

    def test_fizit_added_3_contracts(self):
        delta = self.after_counts["fizit"] - self.before_counts["fizit"]
        self.assertEqual(delta, 3)

    def test_refiner_added_2_contracts(self):
        delta = self.after_counts["refiner"] - self.before_counts["refiner"]
        self.assertEqual(delta, 2)

    def test_supplier1_added_1_contract(self):
        delta = self.after_counts["supplier_1"] - self.before_counts["supplier_1"]
        self.assertEqual(delta, 1)

    def test_supplier2_added_0_contracts(self):
        delta = self.after_counts["supplier_2"] - self.before_counts["supplier_2"]
        self.assertEqual(delta, 0)