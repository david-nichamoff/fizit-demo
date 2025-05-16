from django.core.management.base import BaseCommand
from api.models import ContractApproval


class Command(BaseCommand):
    help = 'Reset approvals for a specific contract (type, idx, release)'

    def add_arguments(self, parser):
        parser.add_argument('--contract_type', type=str, required=True, help='Type of the contract (e.g. purchase, sale)')
        parser.add_argument('--contract_idx', type=int, required=True, help='Index of the contract')
        parser.add_argument('--contract_release', type=int, required=True, help='Release number of the contract')

    def handle(self, *args, **options):
        contract_type = options['contract_type']
        contract_idx = options['contract_idx']
        contract_release = options['contract_release']

        approvals = ContractApproval.objects.filter(
            contract_type=contract_type,
            contract_idx=contract_idx,
            contract_release=contract_release
        )

        if not approvals.exists():
            self.stdout.write(self.style.WARNING(f"No approvals found for {contract_type}:{contract_idx} (release {contract_release})"))
            return

        count = 0
        for a in approvals:
            a.approved = False
            a.approved_by = None
            a.approved_dt = None
            a.save()
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Reset {count} approvals for {contract_type}:{contract_idx} (release {contract_release})"))