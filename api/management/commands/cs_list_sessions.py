import logging
import urllib.parse
import requests
from rest_framework import status

from django.core.management.base import BaseCommand

from api.config import ConfigManager
from api.secrets import SecretsManager
from api.web3.web3_manager import Web3Manager
from api.utilities.logging import log_error, log_info

class Command(BaseCommand):
    help = "List CS Sessions"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)

        # Initialize Config and Web3Manager
        self._initialize()

        try:
            cs_url = self.config_manager.get_cs_url()
            org_id = self.config_manager.get_cs_org_id()
            encoded_org_id = urllib.parse.quote(org_id, safe='')
            log_info(self.logger, f"Initialized CS: cs_url: {cs_url}m, org_id: {org_id}, encoded_org_id: {encoded_org_id}")
         
            # used lower() to workaround a Cubesigner bug where it was not allowing me to submit
            # the transaction. remove the .lower() when this bug is resolved
            api_url = f"{cs_url}/v0/org/{encoded_org_id}/session"

            headers = {
                "Content-Type": "application/json",
                "accept": "application/json",
                "Authorization": "3d6fd7397:MWE4MGExNTAtNzJhNy00YmJlLTg1NjctYTIyY2I1M2VkODNk.eyJlcG9jaF9udW0iOjEsImVwb2NoX3Rva2VuIjoiT3ZOUjl4QWwwUHIzY1JwTlc2ejVPOXJUMVgrTFhrOFA2OFh6YnhoSnpGYz0iLCJvdGhlcl90b2tlbiI6InhwV0JQWEFmMGxvdWxad2F4c3pOeW5WeG1OQm0wZnVkOG9BMm50SjVacTg9In0="
            }

            tx_data = {"role" : "Role#361727aa-353f-46c8-b9fc-2f2f0a23ec25"}
            response = requests.get(api_url, json=self._hexify_tx(tx_data), headers=headers)

            if response.status_code == status.HTTP_200_OK:
                self.stdout.write(self.style.SUCCESS(f"{response.get("sessions", None)}"))
            else:
                self.stdout.write(self.style.ERROR(f"Code: {response.status_code}, Text: {response.text}"))

        except Exception as e:
            log_error(self.logger, f"Error listing session {e}")
            self.stderr.write(self.style.ERROR(f"Error listing session: {str(e)}"))

    def _hexify_tx(self, tx):
        """Convert int values in tx dict to hex strings."""
        return {k: (hex(v) if isinstance(v, int) else v) for k, v in tx.items()}

    def _initialize(self):
        """Initialize ConfigManager, SecretsManager, and Web3Manager."""
        self.config_manager = ConfigManager()
        self.secrets_manager = SecretsManager()
        self.web3_manager = Web3Manager()
        self.web3 = self.web3_manager.get_web3_instance()