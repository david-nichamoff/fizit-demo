import json
import os
import logging

from django.test import TestCase

from api.operations.contract_ops import ContractOperations
from api.operations.party_ops import PartyOperations
from api.operations.settlement_ops import SettlementOperations
from api.operations.transaction_ops import TransactionOperations
from api.operations.artifact_ops import ArtifactOperations
from api.operations.csrf_ops import CsrfOperations
from api.secrets import SecretsManager
from api.config import ConfigManager
from api.utilities.logging import log_info


class SaleEncryptionTest(TestCase):
    def setUp(self):
        # Load fixture data
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures/sale_fiat.json')
        with open(fixture_path, 'r') as file:
            self.fixture_data = json.load(file)

        self.logger = logging.getLogger(__name__)

        # Initialize Secrets and Config Managers
        self.secrets_manager = SecretsManager()
        self.config_manager = ConfigManager()

        self.fizit_master_key = self.secrets_manager.get_master_key()
        self.affiliate_key = self.secrets_manager.get_partner_api_key("Affiliate")
        self.base_url = self.config_manager.get_base_url()

        # Set up headers with Content-Type
        self.common_headers = {'Content-Type': 'application/json'}
        self.fizit_headers = {**self.common_headers, "Authorization": f"Api-Key {self.fizit_master_key}"}
        self.affiliate_headers = {**self.common_headers, "Authorization": f"Api-Key {self.affiliate_key}"}

        # Initialize CSRF token and operations with FIZIT_MASTER_KEY
        self.csrf_ops = CsrfOperations(self.fizit_headers, self.base_url)
        self.csrf_token = self.csrf_ops.get_csrf_token()
        self._initialize_operations(self.fizit_headers)

    def _initialize_operations(self, headers):
        """Initialize operation classes with the provided headers."""
        self.contract_ops = ContractOperations(headers, self.base_url, self.csrf_token)
        self.party_ops = PartyOperations(headers, self.base_url, self.csrf_token)
        self.settlement_ops = SettlementOperations(headers, self.base_url, self.csrf_token)
        self.transaction_ops = TransactionOperations(headers, self.base_url, self.csrf_token)
        self.artifact_ops = ArtifactOperations(headers, self.base_url, self.csrf_token)

    def test_sale_contract_encryption_flow(self):
        # 1. Create a sale contract
        contract_type = self.fixture_data["contract_type"]
        contract_data = self.fixture_data["contract"]
        contract_response = self.contract_ops.post_contract(contract_type, contract_data)
        contract_idx = contract_response.get("contract_idx")

        # 2. Add parties
        parties = self.fixture_data["parties"]
        self.party_ops.post_parties(contract_type, contract_idx, parties)

        # 3. Add settlements
        settlement_data = self.fixture_data["settlements"]
        self.settlement_ops.post_settlements(contract_type, contract_idx, settlement_data)

        # 4. Add transactions
        transaction_data = self.fixture_data["transactions"]
        self.transaction_ops.post_transactions(contract_type, contract_idx, transaction_data)

        # 5. Retrieve and verify with FIZIT_MASTER_KEY (should be decrypted)
        self.verify_encryption(contract_type, contract_idx, self.fizit_headers, should_be_encrypted=False)

        # 6. Retrieve and verify with Affiliate Key (should be encrypted)
        self._initialize_operations(self.affiliate_headers)
        self.verify_encryption(contract_type, contract_idx, self.affiliate_headers, should_be_encrypted=True)

        # 7. Add affiliate party to the contract using FIZIT_MASTER_KEY
        self._initialize_operations(self.fizit_headers)
        affiliate_party = [{"party_code": "Affiliate", "party_type": "affiliate"}]
        self.party_ops.post_parties(contract_type, contract_idx, affiliate_party)

        # 8. Retrieve and verify with Affiliate Key again (should be decrypted now)
        self._initialize_operations(self.affiliate_headers)
        self.verify_encryption(contract_type, contract_idx, self.affiliate_headers, should_be_encrypted=False)

    def verify_encryption(self, contract_type, contract_idx, headers, should_be_encrypted):
        """Verify if fields are encrypted or not based on the `should_be_encrypted` flag."""
        contract_data = self.contract_ops.get_contract(contract_type, contract_idx)
        settlement_data = self.settlement_ops.get_settlements(contract_type, contract_idx)
        transaction_data = self.transaction_ops.get_transactions(contract_type, contract_idx)

        log_info(self.logger, f"Contract data to check: {contract_data}")
        log_info(self.logger, f"Settlement data to check: {settlement_data}")
        log_info(self.logger, f"Transaction data to check: {transaction_data}")

        fields_to_check = {
            "contract.extended_data": contract_data["extended_data"],
            "contract.transact_logic": contract_data["transact_logic"],
            "settlement.extended_data": settlement_data[0]["extended_data"],
            "transaction.extended_data": transaction_data[0]["extended_data"],
            "transaction.transact_data": transaction_data[0]["transact_data"]
        }

        for field, value in fields_to_check.items():
            if should_be_encrypted:
                self.assertEqual(value, "encrypted data", f"{field} should be encrypted.")
            else:
                expected_value = self._get_expected_value(field)
                self.assertEqual(value, expected_value, f"{field} should match the original data.")

    def _get_expected_value(self, field_name):
        """Helper function to fetch the original values from the fixture for comparison."""
        if "contract.extended_data" in field_name:
            return self.fixture_data["contract"]["extended_data"]
        elif "contract.transact_logic" in field_name:
            return self.fixture_data["contract"]["transact_logic"]
        elif "settlement.extended_data" in field_name:
            return self.fixture_data["settlements"][0]["extended_data"]
        elif "transaction.extended_data" in field_name:
            return self.fixture_data["transactions"][0]["extended_data"]
        elif "transaction.transact_data" in field_name:
            return self.fixture_data["transactions"][0]["transact_data"]