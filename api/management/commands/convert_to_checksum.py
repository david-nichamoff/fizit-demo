import logging
from web3 import Web3
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Convert a lowercase Ethereum address to its checksum format"

    def add_arguments(self, parser):
        parser.add_argument("address", type=str, help="The Ethereum address in lowercase to convert to checksum")

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        address = options["address"]

        if not Web3.is_address(address):
            self.stderr.write(self.style.ERROR(f"Invalid Ethereum address: {address}"))
            return

        checksum_address = Web3.to_checksum_address(address)

        self.stdout.write(self.style.SUCCESS(f"Checksum Address: {checksum_address}"))
        logger.info(f"Converted {address} to {checksum_address}")