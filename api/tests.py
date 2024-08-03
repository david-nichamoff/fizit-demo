from django.test import TestCase
from django.core.management import call_command

from api.models import Contract, Party, Transaction

class ContractTests(TestCase):

    def setUp(self):
        call_command('load_contracts')

    def test_contract_loaded(self):
        contract = Contract.objects.get(contract_name="Wastewater Haulage Site 1.0")
        self.assertIsNotNone(contract)
        self.assertEqual(contract.contract_type, "ticketing")

    def test_parties_loaded(self):
        contract = Contract.objects.get(contract_name="Wastewater Haulage Site 1.0")
        parties = Party.objects.filter(contract=contract)
        self.assertEqual(parties.count(), 3)

    def test_transactions_loaded(self):
        contract = Contract.objects.get(contract_name="Wastewater Haulage Site 1.0")
        transactions = Transaction.objects.filter(contract=contract)
        self.assertEqual(transactions.count(), 1)