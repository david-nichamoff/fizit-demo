import os
import json
import logging
import random
import time

from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from dateutil.relativedelta import relativedelta

from django.test import TestCase

from api.operations import ContractOperations, PartyOperations, SettlementOperations
from api.operations import TransactionOperations, CsrfOperations, EventOperations
from api.managers import SecretsManager, ConfigManager

from api.utilities.logging import log_info, log_warning, log_error
from api.utilities.general import generate_random_time

class ContractTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):

        self.secrets_manager = SecretsManager()
        self.config_manager = ConfigManager()

        self.logger = logging.getLogger(__name__)

        self.keys = self.secrets_manager.load_keys()
        self.config = self.config_manager.load_config()

        self.current_date = datetime.now().replace(microsecond=0).isoformat()
        self.headers = {
            'Authorization': f'Api-Key {self.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }

        self.csrf_ops = CsrfOperations(self.headers, self.config)
        self.csrf_token = self.csrf_ops.get_csrf_token()

        self.contract_ops = ContractOperations(self.headers, self.config, self.csrf_token)
        self.party_ops = PartyOperations(self.headers, self.config, self.csrf_token)
        self.settlement_ops = SettlementOperations(self.headers, self.config, self.csrf_token)
        self.transaction_ops = TransactionOperations(self.headers, self.config, self.csrf_token)
        self.event_ops = EventOperations(self.headers, self.config)

        self.delay = 20

    def test_load_contract(self):
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'load_contract_test')
        for filename in os.listdir(fixtures_dir):
            if filename.endswith('.json'):
                with open(os.path.join(fixtures_dir, filename), 'r') as file:
                    try:
                        data = json.load(file)
                        log_info(self.logger,f"Loading contract from file: {filename}")
                        self._run_contract_test(data['contract'], data['parties'], filename)
                    except json.JSONDecodeError as e:
                        self.fail(f'Error decoding JSON from file: {filename}, Error: {str(e)}')
                    except KeyError as e:
                        self.fail(f'Missing key in JSON from file: {filename}, Error: {str(e)}')

    def _run_contract_test(self, contract_data, parties_data, filename):
        contract = self.contract_ops.post_contract(contract_data)
        contract_idx  = contract["contract_idx"]
        self.assertGreaterEqual(contract_idx, 0)
        log_info(self.logger,f'Successfully added contract "{contract_idx}: {contract_data["contract_name"]}"')

        self._validate_contract(contract_idx, contract_data, filename)
        self._manage_parties(contract_idx, parties_data)
        self._manage_settlements(contract_idx, contract_data)
        self._manage_transactions(contract_idx, contract_data)
        self._validate_transaction_financials(contract_idx, contract_data)
        self._validate_settlement_financials(contract_idx, contract_data)
        self._update_and_delete_contract(contract_idx)
        self._validate_events(contract_idx, self.config["contract_addr"], contract_data, parties_data)

    def _validate_contract(self, contract_idx, contract_data, filename):
        contract = self.contract_ops.get_contract(contract_idx)
        self.assertEqual(contract["contract_idx"], contract_idx)
        log_info(self.logger, f"Retrieved contract {contract["contract_idx"]}")

        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'load_contract_test')
        fixture_path = os.path.join(fixtures_dir, filename)
        with open(fixture_path, 'r') as file:
            fixture_data = json.load(file)
            expected_contract_data = fixture_data['contract']

            for field in expected_contract_data:
                self.assertEqual(
                    contract.get(field),
                    expected_contract_data[field],
                    f"Field '{field}' does not match for contract {contract_idx}"
                )

            log_info(self.logger,f"All fields match for contract {contract_idx}")

    def _manage_parties(self, contract_idx, parties_data):
        response = self.party_ops.post_parties(contract_idx, parties_data)
        self.assertGreater(response["count"], 0)

        self._add_test_party(contract_idx)
        self._delete_test_party(contract_idx)
        self._validate_parties(contract_idx, parties_data)

    def _add_test_party(self, contract_idx):
        party_data = {
            "party_code": "UnitTest",
            "party_type": "funder"
        }

        response = self.party_ops.post_parties(contract_idx, [party_data])
        self.assertGreaterEqual(response["count"], 0)

    def _delete_test_party(self, contract_idx):
        parties = self.party_ops.get_parties(contract_idx)
        self.assertGreater(len(parties), 0)
        unit_test_party = next((party for party in parties if party['party_code'] == "UnitTest"), None)

        if unit_test_party is None:
            self.fail(f'No test party found in contract {contract_idx}')

        party_idx = unit_test_party['party_idx']
        response = self.party_ops.delete_party(contract_idx, party_idx)
        self.assertIsNone(response)

        log_info(self.logger,f'Successfully deleted test party from contract {contract_idx}')

    def _validate_parties(self, contract_idx, expected_parties_data):
        parties = self.party_ops.get_parties(contract_idx)
        self.assertGreater(len(parties), 0)

        for expected_party, actual_party in zip(expected_parties_data, parties):
            for field in expected_party:
                self.assertEqual(
                    actual_party.get(field),
                    expected_party[field],
                    f"Field '{field}' does not match for party in contract {contract_idx}"
                )

        log_info(self.logger,f"All parties match for contract {contract_idx}")

    def _manage_settlements(self, contract_idx, contract_data):
        settlements_data = self._generate_settlements(
            contract_data["extended_data"].get("settle_count", 0),
            contract_data["extended_data"].get("first_due_dt"),
            contract_data["extended_data"].get("first_min_dt"),
            contract_data["extended_data"].get("first_max_dt")
        )

        response = self.settlement_ops.post_settlements(contract_idx, settlements_data)
        self.assertEqual(response["count"], len(settlements_data))

    def _manage_transactions(self, contract_idx, contract_data):
        transactions_data = self._generate_transactions(
            contract_idx,
            [contract_data["transact_logic"]['var']],
            {contract_data["transact_logic"]['var']: contract_data["extended_data"][contract_data["transact_logic"]['var']]},
            ['ref_no'],
            contract_data["extended_data"]['first_min_dt'],
            contract_data["extended_data"]['max_txn_dt']
        )

        response = self.transaction_ops.post_transactions(contract_idx, transactions_data)
        self.assertEqual(response["count"], len(transactions_data))

    def _update_and_delete_contract(self, contract_idx):
        patch_data = {"notes": "patched by unit test"}
        response = self.contract_ops.patch_contract(contract_idx, patch_data)
        self.assertEqual(response["contract_idx"], contract_idx)

        # Delete the transactions
        response = self.transaction_ops.delete_transactions(contract_idx)
        self.assertIsNone(response)

        # Delete the settlements
        response = self.settlement_ops.delete_settlements(contract_idx)
        self.assertIsNone(response)

        # Delete the settlements
        response = self.party_ops.delete_parties(contract_idx)
        self.assertIsNone(response)

        # Delete the contract
        response = self.contract_ops.delete_contract(contract_idx)
        self.assertIsNone(response)

    def _load_contract_final_check(self, contract_idx):
        contract = self.contract_ops.get_contract(contract_idx)
        self.assertEqual(contract["contract_idx"], contract_idx)
        self.assertFalse(contract['is_active'], f"Contract {contract_idx} should be inactive")
        self.assertEqual(contract['notes'], "patched by unit test", f"Contract {contract_idx} notes should be 'patched by unit test'")

        log_info(self.logger,f"Contract {contract_idx} final check passed: inactive and notes are correct")

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

        self._validate_event_detail(contract_idx, contract_addr, expected_events, delay=self.delay)

    def _validate_settlement_financials(self, contract_idx, contract_data):
        advance_pct = Decimal(contract_data["advance_pct"])
        residual_pct = (Decimal(1) - advance_pct).quantize(Decimal('0.0001'), rounding=ROUND_DOWN)

        settlements = self.settlement_ops.get_settlements(contract_idx)
        self.assertGreater(len(settlements), 0)

        for settlement in settlements:
            transactions = self.transaction_ops.get_transactions(contract_idx, settlement['transact_min_dt'], settlement['transact_max_dt'])
            self.assertGreater(len(transactions), 0)

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

        log_info(self.logger,f"Settlement financials validation passed for contract {contract_idx}")

    def _validate_transaction_financials(self, contract_idx, contract_data):
        advance_pct = Decimal(contract_data["advance_pct"])
        service_fee_pct = Decimal(contract_data["service_fee_pct"])
        service_fee_amt = Decimal(contract_data["service_fee_amt"])

        transactions = self.transaction_ops.get_transactions(contract_idx)
        self.assertGreater(len(transactions), 0)

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

        log_info(self.logger,f"Transaction financials validation passed for contract {contract_idx}")

    def _validate_event_detail(self, contract_idx, contract_addr, expected_events, delay):
        time.sleep(delay)

        events = self.event_ops.get_events(contract_idx, contract_addr)
        self.assertGreater(len(events), 0)

        event_found = {event_type: False for event_type in expected_events}

        for event in events:
            event_type = event['event_type']
            if event_type in expected_events:
                if event_type in ["SettlementAdded", "TransactionAdded", "PartyDeleted", "PartiesDeleted",
                                "TransactionsDelete","SettlementsDeleted"]:
                    # Simply mark the event as found, without checking event_details
                    event_found[event_type] = True
                    log_info(self.logger,f"{event_type} event found for contract {contract_idx}")
                else:
                    # Handle function-based comparison for other event types
                    if expected_events[event_type](event):
                        event_found[event_type] = True
                        log_info(self.logger,f"{event_type} event found for contract {contract_idx}")

        if all(event_found.values()):
            return event_found
        else:
            log_info(self.logger,f"Not all events found: {event_found}")

        raise AssertionError(f"Failed to validate all expected events for contract {contract_idx}")


    def _generate_settlements(self, settle_count, first_due_dt, first_min_dt, first_max_dt):
        """
        Generate settlement data.

        Args:
            settle_count (int): Number of settlements to generate.
            first_due_dt (str): Start date for settlement due dates.
            first_min_dt (str): Start date for transaction minimum dates.
            first_max_dt (str): Start date for transaction maximum dates.

        Returns:
            list: A list of settlement dictionaries.
        """
        settlements = []
        settle_due_dt = datetime.strptime(first_due_dt, "%Y-%m-%d %H:%M:%S")
        transact_min_dt = datetime.strptime(first_min_dt, "%Y-%m-%d %H:%M:%S")
        transact_max_dt = datetime.strptime(first_max_dt, "%Y-%m-%d %H:%M:%S")

        for _ in range(settle_count):
            settlement = {
                "settle_due_dt": settle_due_dt.strftime("%Y-%m-%d"),
                "transact_min_dt": transact_min_dt.strftime("%Y-%m-%d"),
                "transact_max_dt": transact_max_dt.strftime("%Y-%m-%d"),
                "extended_data": {
                    "ref_no": random.randint(1000, 9999)
                }
            }
            settlements.append(settlement)
            settle_due_dt += relativedelta(months=1)
            transact_min_dt += relativedelta(months=1)
            transact_max_dt += relativedelta(months=1)

        return settlements

    def _generate_transactions(self, contract_idx, variables, sample_values, extended_data_keys, start_date, end_date):
        """
        Generate transaction data.

        Args:
            contract_idx (int): Contract index.
            variables (list): List of variable names.
            sample_values (dict): Sample values for variables.
            extended_data_keys (list): Keys for extended data.
            start_date (str): Start date in ISO 8601 format.
            end_date (str): End date in ISO 8601 format.

        Returns:
            list: A list of transaction dictionaries.
        """
        start_dt = datetime.strptime(start_date.split()[0], "%Y-%m-%d")
        end_dt = datetime.strptime(end_date.split()[0], "%Y-%m-%d") - timedelta(days=1)
        transactions = []
        delta = timedelta(days=1)

        current_dt = start_dt
        while current_dt <= end_dt:
            transact_data = {
                var: round(random.uniform(value * 0.9, value * 1.1), 2) for var, value in sample_values.items()
            }

            extended_data = {key: random.randint(1000, 9999) for key in extended_data_keys}
            random_time = generate_random_time()
            transaction_dt = f"{current_dt.strftime('%Y-%m-%d')} {random_time}"
            transaction = {
                "extended_data": extended_data,
                "transact_dt": datetime.strptime(transaction_dt, '%Y-%m-%d %H:%M:%S').isoformat(),
                "transact_data": transact_data
            }
            transactions.append(transaction)
            current_dt += delta

        return transactions

