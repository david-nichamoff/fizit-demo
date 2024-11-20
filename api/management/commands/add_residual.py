import logging
import time
from django.core.management.base import BaseCommand
from api.managers import SecretsManager, ConfigManager
from api.operations import BankOperations, CsrfOperations

class Command(BaseCommand):
    help = 'Pay residuals for a specific contract_idx based on residual_calc_amt'

    def add_arguments(self, parser):
        # Add contract_idx as an argument with the flag --contract_idx
        parser.add_argument('--contract_idx', type=int, required=True, help='The index of the contract to retrieve and pay residuals for')

    def handle(self, *args, **kwargs):
        contract_idx = kwargs['contract_idx']
        self.logger = logging.getLogger(__name__)

        # Initialize config and secrets
        self._initialize_config()

        try:
            # Retrieve residuals for the specified contract
            self.logger.info(f"Fetching residuals for contract {contract_idx}")
            residuals = self.get_residuals(contract_idx)
            if not residuals:
                self.stdout.write(self.style.WARNING("No residuals found to process."))
                return

            # Process and pay the residuals
            self.logger.info(f"Paying residuals for contract {contract_idx}")
            self.pay_residuals(contract_idx, residuals)

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error processing residuals for contract {contract_idx}: {str(e)}"))
            self.logger.error(f"Error processing residuals for contract {contract_idx}: {str(e)}")

    def _initialize_config(self):
        # Initialize SecretsManager and ConfigManager to load keys and config
        self.secrets_manager = SecretsManager()
        self.config_manager = ConfigManager()

        # Load the keys and config from the respective managers
        self.keys = self.secrets_manager.load_keys()
        self.config = self.config_manager.load_config()

        # Set the headers for making requests, including authorization and content type
        self.headers = {
            'Authorization': f'Api-Key {self.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }

        # Initialize BankOperations and CsrfOperations
        self.bank_ops = BankOperations(self.headers, self.config)
        self.csrf_ops = CsrfOperations(self.headers, self.config)

    def get_residuals(self, contract_idx):
        """Retrieve residuals for a specific contract."""
        response = self.bank_ops.get_residuals(contract_idx)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to retrieve residuals. Status: {response.status_code}\nResponse: {response.text}")

    def pay_residuals(self, contract_idx, residuals):
        """Post residual payment to the API for a specific contract."""
        csrf_token = self.csrf_ops._get_csrf_token()
        response = self.bank_ops.add_residuals(contract_idx, residuals, csrf_token)
        if response.status_code == 201:
            self.stdout.write(self.style.SUCCESS(f"Successfully added residual payment for contract {contract_idx}"))
        else:
            raise Exception(f"Failed to add residual payment. Status: {response.status_code}\nResponse: {response.text}")

        # Confirm the residuals have been processed
        print("Sleeping to ensure that residuals have processed")
        time.sleep(10)  # Wait for the payment processing

        response = self.bank_ops.get_residuals(contract_idx)
        if response.status_code == 200:
            residuals_after_payment = response.json()
            if len(residuals_after_payment) == 0:
                self.stdout.write(self.style.SUCCESS(f"Residuals successfully processed and cleared for contract {contract_idx}"))
            else:
                raise Exception(f"Expected residual count to be 0 after payment, but got {len(residuals_after_payment)}")
        else:
            raise Exception(f"Failed to retrieve residuals after payment. Status: {response.status_code}\nResponse: {response.text}")