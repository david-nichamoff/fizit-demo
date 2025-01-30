from cryptography.fernet import Fernet

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Generates a new AES key and outputs it to stdout for manual intervention'

    def add_arguments(self, parser):
        parser.add_argument(
            '--length',
            type=int,
            default=32,
            help='The length of the generated AES key in bytes (default is 32)'
        )

    def handle(self, *args, **options):
        # Generate AES key
        aes_key = self.generate_aes_key()

        # Output the AES key to stdout for manual handling
        self.stdout.write(self.style.SUCCESS(f'Generated AES key: {aes_key}'))

    def generate_aes_key(self):
        """Generates a new AES key using Fernet."""
        return Fernet.generate_key().decode()  # Generate a key and return it as a string