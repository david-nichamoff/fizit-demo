from cryptography.fernet import Fernet
import boto3
import json
import os
import logging

class EncryptionAPI:
    def __init__(self, encryption_key: bytes):
        """Initialize with an encryption key. Use Fernet symmetric encryption."""
        self.cipher = Fernet(encryption_key)

    def encrypt(self, plain_text: str) -> str:
        """Encrypts plain text data."""
        return self.cipher.encrypt(plain_text.encode()).decode()

    def decrypt(self, encrypted_text: str) -> str:
        """Decrypts encrypted text data."""
        return self.cipher.decrypt(encrypted_text.encode()).decode()

def create_aes_key(secret_name):
    """Generates a new AES key and stores it in AWS Secrets Manager."""
    # Generate a new AES key using Fernet
    new_key = Fernet.generate_key().decode()  # Generates a key and ensures it's a string
    client = boto3.client('secretsmanager')
    
    # Store the new AES key in Secrets Manager
    client.create_secret(
        Name=secret_name,
        SecretString=json.dumps({'aes_key': new_key})
    )
    
    logging.info(f"Created new AES key for {secret_name}")
    return new_key

def get_aes_key(contract_idx):
    env = os.environ.get('FIZIT_ENV', 'dev')  # Default to 'dev' if not set

    # Map the environment to the correct key prefix
    env_mapping = {
        'main': 'mainnet',
        'test': 'testnet',
        'dev': 'devnet'
    }

    # Ensure the environment is valid
    if env not in env_mapping:
        raise ValueError(f"Invalid environment: {env}. Allowed values are 'main', 'test', or 'dev'.")

    # Get the correct environment prefix
    env_prefix = env_mapping[env]

    # Segment keys based on environment
    if env == 'main':
        secret_name = f"{env_prefix}/contract_keys/contract_idx_{contract_idx}"
    else:
        # Reuse a smaller pool of keys for dev and test environments
        shared_key_id = (contract_idx % 5) + 1  # Rotate through 5 shared keys
        secret_name = f"{env_prefix}/contract_keys/shared_key_{shared_key_id}"

    client = boto3.client('secretsmanager')
    
    # Try to retrieve the secret
    try:
        secret_response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(secret_response['SecretString'])
        aes_key = secret['aes_key']
        logging.info(f"Retrieved existing AES key for {secret_name}")
    except client.exceptions.ResourceNotFoundException:
        # If the secret is not found, create a new AES key
        logging.info(f"Secret not found for {secret_name}, creating new AES key.")
        aes_key = create_aes_key(secret_name)

    return aes_key

# Function to instantiate the EncryptionAPI with the AES key fetched from AWS Secrets Manager
def get_encryption_api(contract_idx):
    logging.info(f"Contract to encrypt: {contract_idx}")
    aes_key = get_aes_key(contract_idx)  # Fetch the AES key for this contract
    encryption_key = aes_key.encode()  # Ensure the key is in bytes
    return EncryptionAPI(encryption_key)