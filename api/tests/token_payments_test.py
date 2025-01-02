import os
import json
import time

from decimal import Decimal
from datetime import datetime

from django.test import TestCase
from rest_framework import status

from api.managers import SecretsManager, ConfigManager

from api.operations import ContractOperations, PartyOperations, SettlementOperations
from api.operations import TransactionOperations, CsrfOperations, BankOperations

class PayTokenTests(TestCase):

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
        self.payment_ops = BankOperations(self.headers, self.config)
        self.contract_ops = ContractOperations(self.headers, self.config)
        self.party_ops = PartyOperations(self.headers, self.config)
        self.settlement_ops = SettlementOperations(self.headers, self.config)
        self.transaction_ops = TransactionOperations(self.headers, self.config)
        self.csrf_ops = CsrfOperations(self.headers, self.config)

    def test_token_payments(self):
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'token_payments_test')
        advance_filename = 'pay_advance.json'
        deposit_filename = 'deposit_params.json'
        fixture_path = os.path.join(fixtures_dir, advance_filename)

        with open(fixture_path, 'r') as file:
            try:
                data = json.load(file)
                print(f"Loading contract data from file: {advance_filename}")
                contract_idx = self._test_create_contract(data['contract'])
                self._test_load_parties(contract_idx, data['parties'])
                self._test_load_settlements(contract_idx, data['settlements'])
                self._test_load_transactions(contract_idx, data['transactions'])
                self._test_get_advances(contract_idx, data['contract'])
                self._test_get_deposits(contract_idx, deposit_filename)  
                self._test_get_residuals(contract_idx, data['contract'])
                self._test_compare_settlement_values(contract_idx)
            except json.JSONDecodeError as e:
                self.fail(f'Error decoding JSON from file: {advance_filename}, Error: {str(e)}')
            except KeyError as e:
                self.fail(f'Missing key in JSON from file: {advance_filename}, Error: {str(e)}')

    def _test_create_contract(self, contract_data):
        response = self.contract_ops.load_contract(contract_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Failed to create contract.")
        contract_idx = response.json()
        self.assertIsNotNone(contract_idx, 'Contract index should not be None')
        print(f'Successfully added contract {contract_idx}')
        return contract_idx

    def _test_load_parties(self, contract_idx, parties_data):
        response = self.party_ops.add_parties(contract_idx, parties_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, f"Failed to add parties to contract {contract_idx}.")
        print(f"Parties loaded for contract: {contract_idx}")

    def _test_load_settlements(self, contract_idx, settlements_data):
        response = self.settlement_ops.post_settlements(contract_idx, settlements_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, f"Failed to add settlements to contract {contract_idx}.")
        print(f"Settlements loaded for contract: {contract_idx}")

    def _test_load_transactions(self, contract_idx, transactions_data):
        response = self.transaction_ops.post_transactions(contract_idx, transactions_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, f"Failed to add transactions to contract {contract_idx}.")
        print(f"Transactions loaded for contract: {contract_idx}")

    def _test_get_advances(self, contract_idx, contract_data):
        expected_advance_count = contract_data["extended_data"].get("advance_count")

        # First, get the advances
        response = self.payment_ops.get_advances(contract_idx)
        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed to get advance amount for contract {contract_idx}.")
        advances = response.json()  

        self.assertEqual(
            len(advances),
            expected_advance_count,
            f"Expected advance count {expected_advance_count} does not match actual count {len(advances)} for contract {contract_idx}."
        )

        print(f"Advances loaded for contract: {contract_idx}")

        # Now, call the payment_ops.add_advances function with the advances
        csrf_token = self.csrf_ops._get_csrf_token()
        add_advance_response = self.payment_ops.add_advances(contract_idx, advances, csrf_token)
        self.assertEqual(
            add_advance_response.status_code, 
            status.HTTP_201_CREATED,
            f"Failed to add advances for contract {contract_idx}. Status code: {add_advance_response.status_code}\nResponse: {add_advance_response.text}"
        )

        print(f"Successfully added advances for contract: {contract_idx}")

        print("Sleeping to ensure that advances have processed") 
        time.sleep(10)

        response = self.payment_ops.get_advances(contract_idx)
        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed to get advance amount for contract {contract_idx} after waiting.")

        advances_after_payment = response.json()
        self.assertEqual(
            len(advances_after_payment),
            0,
            f"Expected advance count to be 0 after payment, but got {len(advances_after_payment)} for contract {contract_idx}."
        )

    def _test_get_deposits(self, contract_idx, fixture_filename="deposit_params.json"):
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', "token_payments_test", fixture_filename)

        with open(fixture_path, 'r') as file:
            data = json.load(file)
        
        params = data['params']
        expected_result = data['deposits']

        # Use the payment_ops.get_deposits function to get the deposits
        start_date = params["start_date"]
        end_date = params["end_date"]
        
        response = self.payment_ops.get_deposits(contract_idx, start_date, end_date)
        deposits = response.json()
        
        # Check if one of the deposits matches the expected result
        match_found = False
        for deposit in deposits:
            if (deposit['bank'] == expected_result['bank'] and
                Decimal(deposit['deposit_amt']) == Decimal(expected_result['deposit_amt']) and
                deposit['deposit_dt'] == expected_result['deposit_dt']):

                # Now, call the payment_ops.add_deposits function with the deposits 
                csrf_token = self.csrf_ops._get_csrf_token()
                add_deposit_response = self.payment_ops.add_deposits(contract_idx, [expected_result], csrf_token)
                self.assertEqual(
                    add_deposit_response.status_code, 
                    status.HTTP_201_CREATED,
                    f"Failed to add deposits for contract {contract_idx}. Status code: {add_deposit_response.status_code}\nResponse: {add_deposit_response.text}"
                )

                match_found = True
                break

        self.assertTrue(match_found, f"No matching deposit found for contract {contract_idx}. Expected result: {expected_result}\nReturned deposits: {deposits}")

    def _test_get_residuals(self, contract_idx, contract_data):
        expected_residual_count = contract_data["extended_data"].get("residual_count")

        # First, get the residuals
        response = self.payment_ops.get_residuals(contract_idx)
        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed to get residual amounts for contract {contract_idx}.")

        residuals = response.json()
        self.assertEqual(
            len(residuals),
            expected_residual_count,
            f"Expected residual count {expected_residual_count} does not match actual count {len(residuals)} for contract {contract_idx}."
        )

        print(f"Residuals loaded for contract: {contract_idx}")
        print(f"residuals {residuals}")

        # Now, call the payment_ops.add_residuals function with the residuals
        csrf_token = self.csrf_ops._get_csrf_token()
        add_residuals_response = self.payment_ops.add_residuals(contract_idx, residuals, csrf_token)
        self.assertEqual(
            add_residuals_response.status_code,
            status.HTTP_201_CREATED,
            f"Failed to add residuals for contract {contract_idx}. Status code: {add_residuals_response.status_code}\nResponse: {add_residuals_response.text}"
        )

        print(f"Successfully added residuals for contract: {contract_idx}")

        print("Sleeping to ensure that residuals have processed") 
        time.sleep(10)

        # Get the residuals again after the payment
        response = self.payment_ops.get_residuals(contract_idx)
        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed to get residual amounts for contract {contract_idx} after payment.")
        residuals_after_payment = response.json()

        self.assertEqual(
            len(residuals_after_payment),
            0,
            f"Expected residual count to be 0 after payment, but got {len(residuals_after_payment)} for contract {contract_idx}."
        )

        print(f"Residuals successfully processed and cleared for contract: {contract_idx}")

    def _test_compare_settlement_values(self, contract_idx):
        
        # Assume we want to compare settlement 0
        response = self.settlement_ops.get_settlements(contract_idx)
        if response.status_code != status.HTTP_200_OK:
            self.fail(f'Failed to retrieve settlements for contract {contract_idx}. Status code: {response.status_code}\nResponse: {response.text}')

        settlements = response.json()
        settlement = settlements[0] if settlements else None
        self.assertIsNotNone(settlement, f"No settlements found for contract {contract_idx}.")

        # Load the contract data to compare values
        contract = self.contract_ops.get_contract(contract_idx).json()

        # Compare late_fee_amt
        expected_late_fee_amt = contract['extended_data'].get('late_fee_amt')
        actual_late_fee_amt = settlement.get('late_fee_amt')
        self.assertEqual(
            actual_late_fee_amt,
            expected_late_fee_amt,
            f"Expected late fee amount {expected_late_fee_amt} does not match actual late fee amount {actual_late_fee_amt} for contract {contract_idx}."
        )

        # Compare dispute_amt
        expected_dispute_amt = contract['extended_data'].get('dispute_amt')
        actual_dispute_amt = settlement.get('dispute_amt')
        self.assertEqual(
            actual_dispute_amt,
            expected_dispute_amt,
            f"Expected dispute amount {expected_dispute_amt} does not match actual dispute amount {actual_dispute_amt} for contract {contract_idx}."
        )

        # Compare residual_calc_amt
        expected_residual_calc_amt = contract['extended_data'].get('residual_calc_amt')
        actual_residual_calc_amt = settlement.get('residual_calc_amt')
        self.assertEqual(
            actual_residual_calc_amt,
            expected_residual_calc_amt,
            f"Expected residual calculated amount {expected_residual_calc_amt} does not match actual residual amount {actual_residual_calc_amt} for contract {contract_idx}."
        )

        # Compare residual_pay_amt
        expected_residual_pay_amt = contract['extended_data'].get('residual_calc_amt')
        actual_residual_pay_amt = settlement.get('residual_pay_amt')
        self.assertEqual(
            actual_residual_pay_amt,
            expected_residual_pay_amt,
            f"Expected residual paid amount {expected_residual_pay_amt} does not match actual residual amount {actual_residual_pay_amt} for contract {contract_idx}."
        )

        print(f"Settlement values successfully validated for contract: {contract_idx}")