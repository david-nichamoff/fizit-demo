import os
import subprocess
import time

from django.core.management.base import BaseCommand
from django.conf import settings

from api.managers.config_manager import ConfigManager

class Command(BaseCommand):
    help = 'Deploy smart contracts using Truffle and update the configuration with the new contract address'

    def handle(self, *args, **kwargs):
        # Path to the Truffle directory
        truffle_dir = os.path.join(settings.BASE_DIR, 'truffle')

        # Step 1: Run Truffle Compile
        self.stdout.write(self.style.SUCCESS('Running Truffle Compile...'))
        result = subprocess.run(['truffle', 'compile'], cwd=truffle_dir, capture_output=True, text=True)
        self.stdout.write(result.stdout)
        self.stdout.write(result.stderr)
        if result.returncode != 0:
            self.stdout.write(self.style.ERROR('Truffle compile failed'))
            return

        # Step 2: Run Truffle Migrate with --reset option
        self.stdout.write(self.style.SUCCESS('Running Truffle Migrate...'))
        result = subprocess.run(['truffle', 'migrate', '--network', 'avalanchePrivate', '--reset'], cwd=truffle_dir, capture_output=True, text=True)
        self.stdout.write(result.stdout)
        self.stdout.write(result.stderr)
        if result.returncode != 0:
            self.stdout.write(self.style.ERROR('Truffle migrate failed'))
            return

        # Step 3: Find the New Contract Address
        new_contract_address = self._get_new_contract_address(result.stdout)
        if not new_contract_address:
            self.stdout.write(self.style.ERROR('Failed to find new contract address in Truffle output'))
            return

        # Step 4: Update Configuration with New Contract Address
        self._update_contract_address(new_contract_address)
        self.stdout.write(self.style.SUCCESS(f'Configuration updated with new contract address: {new_contract_address}'))

        # Step 5: Restart services based on environment
        self._restart_services()

    def _get_new_contract_address(self, truffle_output):
        for line in truffle_output.splitlines():
            if 'contract address:' in line:
                return line.split()[-1]
        return None

    def _update_contract_address(self, new_address):
        try:
            config_manager = ConfigManager()
            config_manager.update_config_value('contract_addr', new_address)
            self.stdout.write(self.style.SUCCESS(f'Successfully updated contract address to {new_address}.'))
        except KeyError:
            self.stdout.write(self.style.ERROR('Configuration key "contract_addr" does not exist.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to update configuration: {e}'))

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