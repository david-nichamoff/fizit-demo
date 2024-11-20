import os
import subprocess
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.timezone import now
from api.managers import ConfigManager, SecretsManager
from api.models import Contract

class Command(BaseCommand):
    help = 'Deploy smart contracts using Truffle and update the configuration with the new contract address'

    def handle(self, *args, **kwargs):

        # Initialize Config and Headers
        self._initialize_config()

        # Path to the Truffle directory
        truffle_dir = os.path.join(settings.BASE_DIR, 'truffle')

        # Run Truffle Compile
        self.stdout.write(self.style.SUCCESS('Running Truffle Compile...'))
        result = subprocess.run(['truffle', 'compile'], cwd=truffle_dir, capture_output=True, text=True)
        self.stdout.write(result.stdout)
        self.stdout.write(result.stderr)
        if result.returncode != 0:
            self.stdout.write(self.style.ERROR('Truffle compile failed'))
            return

        # Run Truffle Migrate with --reset option
        self.stdout.write(self.style.SUCCESS('Running Truffle Migrate...'))
        result = subprocess.run(['truffle', 'migrate', '--network', 'avalanchePrivate', '--reset'], cwd=truffle_dir, capture_output=True, text=True)
        self.stdout.write(result.stdout)
        self.stdout.write(result.stderr)
        if result.returncode != 0:
            self.stdout.write(self.style.ERROR('Truffle migrate failed'))
            return

        # Find the New Contract Address
        old_contract_address = self.config['contract_addr']
        new_contract_address = self._get_new_contract_address(result.stdout)
        if not new_contract_address:
            self.stdout.write(self.style.ERROR('Failed to find new contract address in Truffle output'))
            return

        # Update the old contract's expiry date
        self._update_old_contract(old_contract_address)

        # Update Configuration with New Contract Address
        self._update_contract_address(new_contract_address)
        self.stdout.write(self.style.SUCCESS(f'Configuration updated with new contract address: {new_contract_address}'))

        # Add the new contract to the Contract table
        self._add_new_contract(new_contract_address)

        # Restart services based on environment
        self._restart_services()

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

    def _get_new_contract_address(self, truffle_output):
        for line in truffle_output.splitlines():
            if 'contract address:' in line:
                return line.split()[-1]
        return None

    def _update_old_contract(self, old_address):
        if not old_address:
            self.stdout.write(self.style.ERROR('Old contract address not found'))
            return
        try:
            contract = Contract.objects.get(contract_addr=old_address)
            contract.expiry_dt = now()
            contract.save()
            self.stdout.write(self.style.SUCCESS(f'Updated expiry date for old contract {old_address}.'))
        except Contract.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Contract with address {old_address} does not exist.'))

            return
        
    def _update_contract_address(self, new_address):
        try:
            config_manager = ConfigManager()
            config_manager.update_config_value('contract_addr', new_address)
            self.stdout.write(self.style.SUCCESS(f'Successfully updated contract address to {new_address}.'))
        except KeyError:
            self.stdout.write(self.style.ERROR('Configuration key "contract_addr" does not exist.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to update configuration: {e}'))

    def _add_new_contract(self, new_address):
        try:
            Contract.objects.create(
                contract_addr=new_address,
                created_dt=now()
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully added new contract {new_address}.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to add new contract: {e}'))

    def _restart_services(self):
        env = os.getenv('FIZIT_ENV', 'dev')
        self.stdout.write(self.style.SUCCESS(f'Current environment: {env}'))

        if env in ['test', 'main']:
            self.stdout.write(self.style.SUCCESS('Restarting services using supervisorctl...'))
            subprocess.run(['supervisorctl', 'restart', 'project'])
            time.sleep(10)
            subprocess.run(['supervisorctl', 'restart', 'listener'])
            time.sleep(10)
        elif env == 'dev':
            self.stdout.write(self.style.SUCCESS('Restarting services using custom scripts...'))
            stop_script = os.path.join(settings.BASE_DIR, 'stop.sh')
            start_script = os.path.join(settings.BASE_DIR, 'start.sh')
            subprocess.run([stop_script])
            time.sleep(10)
            subprocess.run([start_script])
            time.sleep(10)
        else:
            self.stdout.write(self.style.ERROR(f'Unknown environment: {env}'))