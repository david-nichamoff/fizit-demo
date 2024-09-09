import os
import json

from datetime import datetime
from decimal import Decimal, ROUND_DOWN

from django.test import TestCase
from rest_framework import status

from .operations_contract import ContractOperations
from .operations_party import PartyOperations
from .operations_settlement import SettlementOperations
from .operations_transaction import TransactionOperations
from .operations_csrf import CsrfOperations

from api.managers import SecretsManager, ConfigManager

class TransactionAmountTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        self.secrets_manager = SecretsManager()
        self.config_manager = ConfigManager()

        self.keys = self.secrets_manager.load_keys()
        self.config = self.config_manager.load_config()

        self.current_date = datetime.now().replace(microsecond=0).isoformat()
        self.headers = {
            'Authorization': f'Api-Key {self.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }
        self.contract_ops = ContractOperations(self.headers, self.config)
        self.party_ops = PartyOperations(self.headers, self.config)
        self.settlement_ops = SettlementOperations(self.headers, self.config)
        self.transaction_ops = TransactionOperations(self.headers, self.config)
        self.csrf_ops = CsrfOperations(self.headers, self.config)

        self.delay = 5
        self.retries = 3

    def test_transactions(self):
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_transact_amount')
        for filename in os.listdir(fixtures_dir):
            if filename.endswith('.json'):
                with open(os.path.join(fixtures_dir, filename), 'r') as file:
                    try:
                        data = json.load(file)
                        print(f"Loading data from file: {filename}")
                        self._run_transaction_test(data)
                    except json.JSONDecodeError as e:
                        self.fail(f'Error decoding JSON from file: {filename}, Error: {str(e)}')
                    except KeyError as e:
                        self.fail(f'Missing key in JSON from file: {filename}, Error: {str(e)}')

    def _run_transaction_test(self, data):
        # Load the contract
        response = self.contract_ops.load_contract(data['contract'])
        if response.status_code != status.HTTP_201_CREATED:
            self.fail(f"Failed to load contract. Status code: {response.status_code}\nResponse: {response.text}")

        contract_idx = response.json()
        print(f'Successfully added contract {contract_idx}')

        # Add parties
        response = self.party_ops.add_parties(contract_idx, data['parties'])
        if response.status_code != status.HTTP_201_CREATED:
            self.fail(f"Failed to add parties. Status code: {response.status_code}\nResponse: {response.text}")

        # Add settlements
        response = self.settlement_ops.post_settlements(contract_idx, data['settlements'])
        if response.status_code != status.HTTP_201_CREATED:
            self.fail(f"Failed to add settlements. Status code: {response.status_code}\nResponse: {response.text}")

        # Add transactions
        response = self.transaction_ops.post_transactions(contract_idx, data['transactions'])
        if response.status_code != status.HTTP_201_CREATED:
            self.fail(f"Failed to add transactions. Status code: {response.status_code}\nResponse: {response.text}")

        # Validate settlements
        response = self.settlement_ops.get_settlements(contract_idx)
        if response.status_code != status.HTTP_200_OK:
            self.fail(f"Failed to retrieve settlements. Status code: {response.status_code}\nResponse: {response.text}")

        settlements = response.json()
        self._validate_settlements(settlements)

        # Validate transactions
        response = self.transaction_ops.get_transactions(contract_idx)
        if response.status_code != status.HTTP_200_OK:
            self.fail(f"Failed to retrieve transactions. Status code: {response.status_code}\nResponse: {response.text}")

        transactions = response.json()
        self._validate_transactions(transactions)

    def _validate_settlements(self, settlements):
        for settlement in settlements:
            extended_data = settlement.get("extended_data", {})
            expected_transact_count = extended_data.get("transact_count")
            expected_settle_exp_amt = Decimal(extended_data.get("settle_exp_amt", 0))
            expected_residual_exp_amt = Decimal(extended_data.get("residual_exp_amt", 0))

            # Assert transact_count
            self.assertEqual(
                settlement["transact_count"],
                expected_transact_count,
                f"Expected transact_count to be {expected_transact_count}, but got {settlement['transact_count']}."
            )

            # Assert settle_exp_amt
            actual_settle_exp_amt = Decimal(settlement["settle_exp_amt"])
            self.assertEqual(
                actual_settle_exp_amt.quantize(Decimal('0.01'), rounding=ROUND_DOWN),
                expected_settle_exp_amt.quantize(Decimal('0.01'), rounding=ROUND_DOWN),
                f"Expected settle_exp_amt to be {expected_settle_exp_amt}, but got {actual_settle_exp_amt}."
            )

            # Assert residual_exp_amt
            actual_residual_exp_amt = Decimal(settlement["residual_exp_amt"])
            self.assertEqual(
                actual_residual_exp_amt.quantize(Decimal('0.01'), rounding=ROUND_DOWN),
                expected_residual_exp_amt.quantize(Decimal('0.01'), rounding=ROUND_DOWN),
                f"Expected residual_exp_amt to be {expected_residual_exp_amt}, but got {actual_residual_exp_amt}."
            )

        print("All settlement validations passed.")

    def _validate_transactions(self, transactions):
        for transaction in transactions:
            extended_data = transaction.get("extended_data", {})
            expected_advance_amt = Decimal(extended_data.get("advance_amt", 0))
            expected_service_fee_amt = Decimal(extended_data.get("service_fee_amt", 0))

            # Assert advance_amt
            actual_advance_amt = Decimal(transaction["advance_amt"])
            self.assertEqual(
                actual_advance_amt.quantize(Decimal('0.01'), rounding=ROUND_DOWN),
                expected_advance_amt.quantize(Decimal('0.01'), rounding=ROUND_DOWN),
                f"Expected advance_amt to be {expected_advance_amt}, but got {actual_advance_amt}."
            )

            # Assert service_fee_amt
            actual_service_fee_amt = Decimal(transaction["service_fee_amt"])
            self.assertEqual(
                actual_service_fee_amt.quantize(Decimal('0.01'), rounding=ROUND_DOWN),
                expected_service_fee_amt.quantize(Decimal('0.01'), rounding=ROUND_DOWN),
                f"Expected service_fee_amt to be {expected_service_fee_amt}, but got {actual_service_fee_amt}."
            )

        print("All transaction validations passed.")