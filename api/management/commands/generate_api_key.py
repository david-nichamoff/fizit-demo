import secrets
import string
import os
import boto3
import json

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Generates a new API key, stores it in AWS Secrets Manager, and sets up rotation'

    def add_arguments(self, parser):
        parser.add_argument(
            'party_code',
            type=str,
            help='The party code to associate with the API key'
        )
        parser.add_argument(
            '--length',
            type=int,
            default=32,
            help='Length of the generated API key (default is 32 characters)'
        )

    def handle(self, *args, **options):
        party_code = options['party_code']
        length = options['length']
        new_api_key = self.generate_api_key(length)

        # Get environment and secret name
        env = os.environ.get('FIZIT_ENV', 'dev')  # Default to 'dev'
        secret_name = f"{env}net/api-key-{party_code}"

        # Store the API key in AWS Secrets Manager
        self.store_api_key(secret_name, new_api_key, party_code)

        # Setup rotation after storing the key
        self.setup_rotation(secret_name, party_code)

        # Output the generated API key
        self.stdout.write(self.style.SUCCESS(f'Generated API Key: {new_api_key}'))
        self.stdout.write(self.style.SUCCESS(f'Successfully stored API key for party code "{party_code}" in secret "{secret_name}"'))

    def generate_api_key(self, length=32):
        """Generates a random API key with the specified length."""
        charset = string.ascii_letters + string.digits  # Uppercase, lowercase, and digits
        return ''.join(secrets.choice(charset) for _ in range(length))

    def store_api_key(self, secret_name, api_key, party_code):
        """Stores the generated API key in AWS Secrets Manager with the specified secret name."""
        client = boto3.client('secretsmanager')

        # Define the secret value to store
        secret_value = {
            'api_key': api_key
        }

        # Create the secret in AWS Secrets Manager
        try:
            client.create_secret(
                Name=secret_name,
                SecretString=json.dumps(secret_value),
                Description=f"{party_code} API key"  # Description with the party_code
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created secret "{secret_name}"'))
        except client.exceptions.ResourceExistsException:
            self.stdout.write(self.style.WARNING(f'Secret "{secret_name}" already exists, updating the API key'))
            client.put_secret_value(
                SecretId=secret_name,
                SecretString=json.dumps(secret_value)
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to store API key: {str(e)}'))

    def setup_rotation(self, secret_name, party_code):
        """Sets up rotation for the secret in AWS Secrets Manager."""
        client = boto3.client('secretsmanager')

        try:
            client.rotate_secret(
                SecretId=secret_name,
                RotationLambdaARN='arn:aws:lambda:us-east-1:549601943297:function:rotate-secret-function',
                RotationRules={
                    'AutomaticallyAfterDays': 60 
                }
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully set up rotation for secret "{secret_name}" with 30-day rotation'))
        except client.exceptions.ResourceNotFoundException:
            self.stdout.write(self.style.ERROR(f'Secret "{secret_name}" not found for rotation setup'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to set up rotation: {str(e)}'))
