import os
import json

from datetime import datetime
from decimal import Decimal, ROUND_DOWN

from django.test import TestCase
from rest_framework import status

from .contract_operations import ContractOperations
from .party_operations import PartyOperations
from .settlement_operations import SettlementOperations
from .transaction_operations import TransactionOperations
from .utils import Utils
from .validate_events import validate_events

import packages.load_keys as load_keys
import packages.load_config as load_config

keys = load_keys.load_keys()
config = load_config.load_config()

class ContractTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        self.current_date = datetime.now().replace(microsecond=0).isoformat()
        self.headers = {
            'Authorization': f'Api-Key {keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }
        self.contract_ops = ContractOperations(self.headers, config)
        self.party_ops = PartyOperations(self.headers, config)
        self.settlement_ops = SettlementOperations(self.headers, config)
        self.transaction_ops = TransactionOperations(self.headers, config)
        self.utils = Utils(self.headers, config)
        self.delay = 5
        self.retries = 3

    def test_load_contracts(self):
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_load_contracts')
        for filename in os.listdir(fixtures_dir):
            if filename.endswith('.json'):
                with open(os.path.join(fixtures_dir, filename), 'r') as file:
                    try:
                        data = json.load(file)
                        print(f"Loading contract from file: {filename}")
                        self._run_contract_test(data['contract'], data['parties'], filename)
                    except json.JSONDecodeError as e:
                        self.fail(f'Error decoding JSON from file: {filename}, Error: {str(e)}')
                    except KeyError as e:
                        self.fail(f'Missing key in JSON from file: {filename}, Error: {str(e)}')

    def _run_contract_test(self, contract_data, parties_data, filename):
        response = self.contract_ops.load_contract(contract_data)

        if response.status_code == status.HTTP_201_CREATED:
            try:
                contract_idx = response.json()
                self.assertIsNotNone(contract_idx, 'Contract index should not be None')
                print(f'Successfully added contract "{contract_idx}: {contract_data["contract_name"]}"')

                self._validate_contract(contract_idx, contract_data, filename)
                self._manage_parties(contract_idx, parties_data)
                self._manage_settlements(contract_idx, contract_data)
                self._manage_transactions(contract_idx, contract_data)

                self._validate_transaction_financials(contract_idx, contract_data)
                self._validate_settlement_financials(contract_idx, contract_data)

                #self._update_and_delete_contract(contract_idx)
                #self._validate_events(contract_idx, config["contract_addr"], contract_data, parties_data)

            except json.JSONDecodeError:
                self.fail('Failed to parse JSON response from the server')
        else:
            self.fail(f'Failed to add contract "{contract_data["contract_name"]}". Status code: {response.status_code}\nHeaders: {self.headers}\nPayload: {json.dumps(contract_data)}\nResponse: {response.text}')

    def _validate_contract(self, contract_idx, contract_data, filename):
        response = self.contract_ops.get_contract(contract_idx)
        if response.status_code != status.HTTP_200_OK:
            self.fail(f'Failed to get contract {contract_idx}. Status code: {response.status_code}\nResponse: {response.text}')

        contract_data_response = response.json()

        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_load_contracts')
        fixture_path = os.path.join(fixtures_dir, filename)
        with open(fixture_path, 'r') as file:
            fixture_data = json.load(file)
            expected_contract_data = fixture_data['contract']

            for field in expected_contract_data:
                self.assertEqual(
                    contract_data_response.get(field), 
                    expected_contract_data[field], 
                    f"Field '{field}' does not match for contract {contract_idx}"
                )

            print(f"All fields match for contract {contract_idx}")

    def _manage_parties(self, contract_idx, parties_data):
        response = self.party_ops.add_parties(contract_idx, parties_data)
        if response.status_code == status.HTTP_201_CREATED:
            print(f'Successfully added parties to contract {contract_idx}')
        else:
            self.fail(f'Failed to add parties to contract {contract_idx}. Status code: {response.status_code}\nHeaders: {self.headers}\nPayload: {json.dumps(parties_data)}\nResponse: {response.text}')

        self._add_test_party(contract_idx)
        self._delete_test_party(contract_idx)
        self._validate_parties(contract_idx, parties_data)

    def _add_test_party(self, contract_idx):
        party_data = {
            "party_code": "UnitTest",
            "party_type": "Funder"
        }

        response = self.party_ops.add_parties(contract_idx, [party_data])
        if response.status_code == status.HTTP_201_CREATED:
            print(f'Successfully added test party to contract {contract_idx}')
        else:
            self.fail(f'Failed to add test party to contract {contract_idx}. Status code: {response.status_code}\nResponse: {response.text}')

    def _delete_test_party(self, contract_idx):
        response = self.party_ops.get_parties(contract_idx)

        if response.status_code != status.HTTP_200_OK:
            self.fail(f'Failed to retrieve parties for contract {contract_idx}. Status code: {response.status_code}\nResponse: {response.content.decode("utf-8")}')

        parties_data = response.json()
        unit_test_party = next((party for party in parties_data if party['party_code'] == "UnitTest"), None)

        if unit_test_party is None:
            self.fail(f'No test party found in contract {contract_idx}')

        party_idx = unit_test_party['party_idx']

        csrf_token = self.utils._get_csrf_token()
        delete_response = self.party_ops.delete_party(contract_idx, party_idx, csrf_token, self.retries, self.delay)

        if delete_response.status_code != status.HTTP_204_NO_CONTENT:
            self.fail(f'Failed to delete test party from contract {contract_idx}. Status code: {delete_response.status_code}\nResponse: {delete_response.content.decode("utf-8")}')
        else:
            print(f'Successfully deleted test party from contract {contract_idx}')

    def _validate_parties(self, contract_idx, expected_parties_data):
        response = self.party_ops.get_parties(contract_idx)
        if response.status_code != status.HTTP_200_OK:
            self.fail(f'Failed to get parties for contract {contract_idx}. Status code: {response.status_code}\nResponse: {response.text}')

        parties_data_response = response.json()

        for expected_party, actual_party in zip(expected_parties_data, parties_data_response):
            for field in expected_party:
                self.assertEqual(
                    actual_party.get(field),
                    expected_party[field],
                    f"Field '{field}' does not match for party in contract {contract_idx}"
                )

        print(f"All parties match for contract {contract_idx}")

    def _manage_settlements(self, contract_idx, contract_data):
        settlements_data = self.settlement_ops.generate_settlements(
            contract_data["extended_data"].get("settle_count", 0),
            contract_data["extended_data"].get("first_due_dt"),
            contract_data["extended_data"].get("first_min_dt"),
            contract_data["extended_data"].get("first_max_dt")
        )

        response = self.settlement_ops.post_settlements(contract_idx, settlements_data)
        if response.status_code == status.HTTP_201_CREATED:
            print(f'Successfully added settlements to contract {contract_idx}')
        else:
            self.fail(f'Failed to add settlements to contract {contract_idx}. Status code: {response.status_code}\nResponse: {response.text}')

    def _manage_transactions(self, contract_idx, contract_data):
        transactions_data = self.transaction_ops.generate_transactions(
            contract_idx,
            [contract_data["transact_logic"]['var']],
            {contract_data["transact_logic"]['var']: contract_data["extended_data"][contract_data["transact_logic"]['var']]},
            ['ref_no'],
            contract_data["extended_data"]['first_min_dt'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        response = self.transaction_ops.post_transactions(contract_idx, transactions_data)
        if response.status_code == status.HTTP_201_CREATED:
            print(f"Batch of transactions successfully created.")
        else:
            self.fail(f"Failed to create batch of transactions. Status code: {response.status_code}\nResponse: {response.content.decode('utf-8')}")

    def _update_and_delete_contract(self, contract_idx):
        # Patch the contract
        patch_data = {"notes": "patched by unit test"}
        response = self.contract_ops.patch_contract(contract_idx, patch_data)
        if response.status_code == status.HTTP_200_OK:
            print(f'Successfully patched contract {contract_idx}')
        else:
            self.fail(f'Failed to patch contract {contract_idx}. Status code: {response.status_code}\nResponse: {response.text}')

        # Delete the transactions
        csrf_token = self.utils._get_csrf_token()
        response = self.transaction_ops.delete_transactions(contract_idx, csrf_token)
        if response.status_code == status.HTTP_204_NO_CONTENT:
            print(f'Successfully deleted transactions for contract {contract_idx}')
        else:
            self.fail(f'Failed to delete transactions for contract {contract_idx}. Status code: {response.status_code}\nResponse: {response.text}')

        # Delete the settlements
        csrf_token = self.utils._get_csrf_token()
        response = self.settlement_ops.delete_settlements(contract_idx, csrf_token)
        if response.status_code == status.HTTP_204_NO_CONTENT:
            print(f'Successfully deleted settlements for contract {contract_idx}')
        else:
            self.fail(f'Failed to delete settlements for contract {contract_idx}. Status code: {response.status_code}\nResponse: {response.text}')

        # Delete the settlements
        csrf_token = self.utils._get_csrf_token()
        response = self.party_ops.delete_parties(contract_idx, csrf_token)
        if response.status_code == status.HTTP_204_NO_CONTENT:
            print(f'Successfully deleted parties for contract {contract_idx}')
        else:
            self.fail(f'Failed to delete parties for contract {contract_idx}. Status code: {response.status_code}\nResponse: {response.text}')

        # Delete the contract
        response = self.contract_ops.delete_contract(contract_idx)
        if response.status_code == status.HTTP_204_NO_CONTENT:
            print(f'Successfully deleted contract {contract_idx}')
        else:
            self.fail(f'Failed to delete contract {contract_idx}. Status code: {response.status_code}\nResponse: {response.text}')

    def _load_contract_final_check(self, contract_idx):
        response = self.contract_ops.get_contract(contract_idx)
        if response.status_code != status.HTTP_200_OK:
            self.fail(f'Failed to retrieve contract {contract_idx}. Status code: {response.status_code}\nResponse: {response.text}')

        contract_data = response.json()
        self.assertFalse(contract_data['is_active'], f"Contract {contract_idx} should be inactive")
        self.assertEqual(contract_data['notes'], "patched by unit test", f"Contract {contract_idx} notes should be 'patched by unit test'")
        print(f"Contract {contract_idx} final check passed: inactive and notes are correct")

    def _validate_events(self, contract_idx, contract_addr, contract_data, parties_data):
        expected_events = {
            "ContractAdded": lambda event: event['details'] == contract_data["contract_name"],
            "PartyAdded": lambda event: event['details'] in [party['party_code'] for party in parties_data if party['party_code'] != "UnitTest"],
            "PartyDeleted": lambda event: True,  
            "SettlementAdded": lambda event: True, 
            "TransactionAdded": lambda event: True,  
            "ContractUpdated": lambda event: event['details'].startswith("notes:") and event['details'].endswith("->patched by unit test"),
            "ContractDeleted": lambda event: event['details'] == str(contract_idx),
            "TransactionsDeleted": lambda event: True,
            "SettlementsDeleted": lambda event: True,
            "PartiesDeleted": lambda event: True,
        }

        validate_events(contract_idx, contract_addr, self.headers, expected_events, retries=self.retries, delay=self.delay)

    def _validate_settlement_financials(self, contract_idx, contract_data):
        advance_pct = Decimal(contract_data["advance_pct"])
        residual_pct = (Decimal(1) - advance_pct).quantize(Decimal('0.0001'), rounding=ROUND_DOWN)

        response = self.settlement_ops.get_settlements(contract_idx)
        if response.status_code != status.HTTP_200_OK:
            self.fail(f'Failed to retrieve settlements for contract {contract_idx}. Status code: {response.status_code}\nResponse: {response.text}')

        settlements = response.json()

        for settlement in settlements:
            response = self.transaction_ops.get_transactions(contract_idx, settlement['transact_min_dt'], settlement['transact_max_dt'])
            if response.status_code != status.HTTP_200_OK:
                self.fail(f'Failed to retrieve transactions for contract {contract_idx} between {settlement["transact_min_dt"]} and {settlement["transact_max_dt"]}. Status code: {response.status_code}\nResponse: {response.text}')

            transactions = response.json()

            # Calculate the total transaction amount as Decimal
            total_transact_amt = sum(Decimal(transaction['transact_amt']) for transaction in transactions)
            total_transact_amt = Decimal(total_transact_amt).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

            self.assertEqual(
                Decimal(settlement['settle_exp_amt']).quantize(Decimal('0.01'), rounding=ROUND_DOWN),
                total_transact_amt,
                f"Settlement {settlement['settle_idx']} settle_exp_amt does not match the sum of transaction amounts"
            )

            # Assert the transaction count
            transact_count = len(transactions)
            self.assertEqual(
                settlement['transact_count'], 
                transact_count,
                f"Settlement {settlement['settle_idx']} transact_count ({settlement['transact_count']}) does not match the number of transactions ({transact_count})"
            )

            # Calculate the expected residual amount
            expected_residual_amt = Decimal(settlement['settle_exp_amt']) - Decimal(settlement['advance_amt_gross'])

            self.assertEqual(
                Decimal(settlement['residual_exp_amt']).quantize(Decimal('0.01'), rounding=ROUND_DOWN),
                expected_residual_amt,
                f"Settlement {settlement['settle_idx']} residual_exp_amt ({settlement['residual_exp_amt']}) does not match the expected residual amount ({expected_residual_amt})"
            )

        print(f"Settlement financials validation passed for contract {contract_idx}")

    def _validate_transaction_financials(self, contract_idx, contract_data):
        advance_pct = Decimal(contract_data["advance_pct"])
        service_fee_pct = Decimal(contract_data["service_fee_pct"])
        service_fee_amt = Decimal(contract_data["service_fee_amt"])

        response = self.transaction_ops.get_transactions(contract_idx)
        if response.status_code != status.HTTP_200_OK:
            self.fail(f'Failed to retrieve transactions for contract {contract_idx}. Status code: {response.status_code}\nResponse: {response.text}')
        
        transactions = response.json()

        for transaction in transactions:
            transact_amt = Decimal(transaction['transact_amt'])
            
            if transact_amt > 0:
                # Calculate the service fee
                service_fee = (service_fee_pct * transact_amt) + service_fee_amt
                service_fee = service_fee.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

                # Calculate the advance amount
                advance_amt = (transact_amt * advance_pct) - service_fee
                advance_amt = max(advance_amt, Decimal(0))
                advance_amt = advance_amt.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

                self.assertEqual(Decimal(transaction['advance_amt']).quantize(Decimal('0.01'), rounding=ROUND_DOWN), advance_amt,
                                f"Transaction {transaction['transact_idx']} advance_amt does not match the expected advance amount")

        print(f"Transaction financials validation passed for contract {contract_idx}")