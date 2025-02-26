import logging
import requests
from django.core.management.base import BaseCommand
from api.config import ConfigManager
from api.secrets import SecretsManager
from api.web3.web3_manager import Web3Manager
from api.models import ContractSnapshot
from api.operations import ContractOperations, CsrfOperations
from api.utilities.logging import log_info, log_error

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Populate transact_logic for existing contracts in ContractSnapshot"

    def handle(self, *args, **options):
        self._initialize()
        self.stdout.write(self.style.NOTICE("Fetching contracts that need transact_logic..."))
        contracts = ContractSnapshot.objects.filter(transact_logic={})  

        if not contracts.exists():
            self.stdout.write(self.style.SUCCESS("All contracts already have transact_logic populated."))
            return

        self.stdout.write(self.style.NOTICE(f"Updating {contracts.count()} contracts..."))

        updated_count = 0
        for contract in contracts:
            try:
                contract_data = self.contract_ops.get_contract(contract.contract_type, contract.contract_idx)
                transact_logic = contract_data["transact_logic"]

                if transact_logic:
                    contract.transact_logic = transact_logic
                    contract.save(update_fields=["transact_logic"])
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Updated contract {contract.contract_idx}"))

            except Exception as e:
                log_error(logger, f"Failed to fetch transact_logic for contract {contract.contract_idx}: {e}")
                self.stderr.write(self.style.ERROR(f"Failed to update contract {contract.contract_idx}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully updated {updated_count} contracts."))

    def _initialize(self):
        """Initialize configuration and headers."""
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()
        self.secrets_manager = SecretsManager()
        self.web3_manager = Web3Manager()

        # Prepare headers for API requests
        self.headers = {
            'Authorization': f'Api-Key {self.secrets_manager.get_master_key()}',
            'Content-Type': 'application/json'
        }

        self.base_url = self.config_manager.get_base_url()
        self.csrf_ops = CsrfOperations(self.headers, self.base_url)
        self.csrf_token = self.csrf_ops.get_csrf_token()
        self.contract_ops = ContractOperations(self.headers, self.base_url, self.csrf_token)


    def fetch_transact_logic(self, contract_type, contract_idx):
        """Retrieve transact_logic from the blockchain using Web3Manager."""
        try:
            return self.web3_manager.get_transact_logic(contract_idx)
        except Exception as e:
            log_error(logger, f"Error fetching transact_logic for contract {contract_idx}: {e}")
            return None