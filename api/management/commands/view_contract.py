import logging
from django.core.management.base import BaseCommand
from api.managers import Web3Manager, ConfigManager

class Command(BaseCommand):
    help = 'Retrieve contract details, settlements, parties, transactions, and artifacts for a specific contract_idx from the blockchain'

    def add_arguments(self, parser):
        parser.add_argument('contract_idx', type=int, help='The index of the contract to retrieve')

    def handle(self, *args, **kwargs):
        contract_idx = kwargs['contract_idx']
        self.logger = logging.getLogger(__name__)

        # Initialize managers and retrieve data from blockchain
        w3_manager = Web3Manager()
        config_manager = ConfigManager()
        w3 = w3_manager.get_web3_instance()
        w3_contract = w3_manager.get_web3_contract()

        try:
            self.logger.info(f"Fetching data for contract {contract_idx}")
            contract_data = self.get_contract_data(w3_contract, contract_idx)
            settlements = self.get_settlements(w3_contract, contract_idx)
            parties = self.get_parties(w3_contract, contract_idx)
            transactions = self.get_transactions(w3_contract, contract_idx)
            artifacts = self.get_artifacts(w3_contract, contract_idx)

            # Print the data
            self.display_contract_data(contract_data)
            self.display_settlements(settlements)
            self.display_parties(parties)
            self.display_transactions(transactions)
            self.display_artifacts(artifacts)

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error retrieving data: {str(e)}"))
            self.logger.error(f"Error retrieving data for contract {contract_idx}: {str(e)}")

    def get_contract_data(self, w3_contract, contract_idx):
        """Retrieve raw contract data from the blockchain."""
        contract = w3_contract.functions.getContract(contract_idx).call()

        # Build a dictionary of contract data, directly from the blockchain, without formatting
        contract_data = {
            "contract_idx": contract_idx,
            "extended_data": contract[0],  # Raw data as it is on-chain
            "contract_name": contract[1],
            "contract_type": contract[2],
            "funding_instr": contract[3],  # Raw data as it is on-chain
            "service_fee_pct": contract[4],  # Unformatted
            "service_fee_max": contract[5],  # Unformatted
            "service_fee_amt": contract[6],  # Unformatted
            "advance_pct": contract[7],      # Unformatted
            "late_fee_pct": contract[8],     # Unformatted
            "transact_logic": contract[9],   # Raw data as it is on-chain
            "min_threshold": contract[10],   # Unformatted
            "max_threshold": contract[11],   # Unformatted
            "notes": contract[12],
            "is_active": contract[13],
            "is_quote": contract[14],
        }
        return contract_data

    def get_settlements(self, w3_contract, contract_idx):
        """Retrieve raw settlements for the contract from the blockchain."""
        settlements = w3_contract.functions.getSettlements(contract_idx).call()
        settlements_data = []
        for settlement in settlements:
            settlement_data = {
                "extended_data": settlement[0],
                "settle_due_dt": settlement[1],
                "transact_min_dt": settlement[2],
                "transact_max_dt": settlement[3],
                "transact_count": settlement[4],
                "advance_amt": settlement[5],
                "advance_amt_gross": settlement[6],
                "settle_pay_dt": settlement[7],
                "settle_exp_amt": settlement[8],
                "settle_pay_amt": settlement[9],
                "settle_confirm": settlement[10],
                "dispute_amt": settlement[11],
                "dispute_reason": settlement[12],
                "days_late": settlement[13],
                "late_fee_amt": settlement[14],
                "residual_pay_dt": settlement[15],
                "residual_pay_amt": settlement[16],
                "residual_confirm": settlement[17],
                "residual_exp_amt": settlement[18],
                "residual_calc_amt": settlement[19]
            }
            settlements_data.append(settlement_data)
        return settlements_data

    def get_parties(self, w3_contract, contract_idx):
        """Retrieve raw parties for the contract from the blockchain."""
        parties = w3_contract.functions.getParties(contract_idx).call()
        parties_data = []
        for party in parties:
            party_data = {
                "party_code": party[0],
                "party_address": party[1],
                "party_type": party[2]
            }
            parties_data.append(party_data)
        return parties_data

    def get_transactions(self, w3_contract, contract_idx):
        """Retrieve raw transactions for the contract from the blockchain."""
        transactions = w3_contract.functions.getTransactions(contract_idx).call()
        transactions_data = []
        for transaction in transactions:
            transaction_data = {
                "extended_data": transaction[0],
                "transact_dt": transaction[1],
                "transact_amt": transaction[2],
                "service_fee_amt": transaction[3],
                "advance_amt": transaction[4],
                "transact_data": transaction[5],
                "advance_pay_dt": transaction[6],
                "advance_pay_amt": transaction[7],
                "advance_confirm": transaction[8]
            }
            transactions_data.append(transaction_data)
        return transactions_data

    def get_artifacts(self, w3_contract, contract_idx):
        """Retrieve raw artifacts for the contract from the blockchain."""
        artifacts = w3_contract.functions.getArtifacts(contract_idx).call()
        artifacts_data = []
        for artifact in artifacts:
            artifact_data = {
                "doc_title": artifact[0],
                "doc_type": artifact[1],
                "added_dt": artifact[2],
                "s3_bucket": artifact[3],
                "s3_object_key": artifact[4],
                "s3_version_id": artifact[5]
            }
            artifacts_data.append(artifact_data)
        return artifacts_data

    def display_contract_data(self, contract_data):
        """Display contract data in an easy-to-read format."""
        self.stdout.write(self.style.SUCCESS("\n--- Contract Data ---"))
        for key, value in contract_data.items():
            self.stdout.write(f"{key}: {value}")

    def display_settlements(self, settlements):
        """Display settlements in an easy-to-read format."""
        self.stdout.write(self.style.SUCCESS("\n--- Settlements ---"))
        for idx, settlement in enumerate(settlements):
            self.stdout.write(self.style.SUCCESS(f"Settlement {idx + 1}:"))
            for key, value in settlement.items():
                self.stdout.write(f"{key}: {value}")

    def display_parties(self, parties):
        """Display parties in an easy-to-read format."""
        self.stdout.write(self.style.SUCCESS("\n--- Parties ---"))
        for idx, party in enumerate(parties):
            self.stdout.write(self.style.SUCCESS(f"Party {idx + 1}:"))
            for key, value in party.items():
                self.stdout.write(f"{key}: {value}")

    def display_transactions(self, transactions):
        """Display transactions in an easy-to-read format."""
        self.stdout.write(self.style.SUCCESS("\n--- Transactions ---"))
        for idx, transaction in enumerate(transactions):
            self.stdout.write(self.style.SUCCESS(f"Transaction {idx + 1}:"))
            for key, value in transaction.items():
                self.stdout.write(f"{key}: {value}")

    def display_artifacts(self, artifacts):
        """Display artifacts in an easy-to-read format."""
        self.stdout.write(self.style.SUCCESS("\n--- Artifacts ---"))
        for idx, artifact in enumerate(artifacts):
            self.stdout.write(self.style.SUCCESS(f"Artifact {idx + 1}:"))
            for key, value in artifact.items():
                self.stdout.write(f"{key}: {value}")