import secrets
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Generates a new API key and logs it'

    def add_arguments(self, parser):
        parser.add_argument(
            '--length',
            type=int,
            default=32,
            help='Length of the generated API key (default is 32 characters)'
        )

    def handle(self, *args, **options):
        length = options['length']
        new_api_key = self.generate_api_key(length)
        self.stdout.write(self.style.SUCCESS(f'Generated API Key: {new_api_key}'))

    def generate_api_key(self, length=32):
        return secrets.token_urlsafe(length)