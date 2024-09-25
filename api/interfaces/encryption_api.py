from cryptography.fernet import Fernet
import boto3
import json
import os
import logging

class EncryptionAPI:
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)

    def encrypt(self, data: dict) -> str:
        json_str = json.dumps(data)
        encrypted_text = self.cipher.encrypt(json_str.encode())
        return encrypted_text.decode()

    def decrypt(self, encrypted_text: str) -> dict:
        decrypted_text = self.cipher.decrypt(encrypted_text.encode()).decode()
        return json.loads(decrypted_text)

def create_aes_key():
    """Generates a new AES key."""
    return Fernet.generate_key().decode()  # Generate a key and ensure it's a string

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
    secret_name = f"{env_prefix}/contract-keys"

    client = boto3.client('secretsmanager')
    
    # Try to retrieve the secret that contains all keys for the environment
    try:
        secret_response = client.get_secret_value(SecretId=secret_name)
        secrets = json.loads(secret_response['SecretString'])
        logging.info(f"Retrieved existing AES keys for {secret_name}")

        # Logic for retrieving the correct key based on the environment
        if env == 'main':
            key_name = f"contract_key_{contract_idx}"
            aes_key = secrets.get(key_name)
            if not aes_key or aes_key == "dummy":
                # Generate a new AES key if it's missing or set to "dummy"
                logging.info(f"Contract-specific key not found or is 'dummy' for {key_name}, generating a new key.")
                aes_key = create_aes_key()
                secrets[key_name] = aes_key
                update_aes_keys(secret_name, secrets) 
        else:
            shared_key_id = (contract_idx % 5) + 1  # Rotate through shared keys
            aes_key = secrets.get(f"shared_key_{shared_key_id}")

            if not aes_key or aes_key == "dummy":
                logging.info(f"Shared key not found or is 'dummy' for shared_key_{shared_key_id}, generating a new key.")
                aes_key = create_aes_key()
                secrets[f"shared_key_{shared_key_id}"] = aes_key
                update_aes_keys(secret_name, secrets)

    except client.exceptions.ResourceNotFoundException:
        logging.error(f"Secret not found for {secret_name}.")
        raise

    return aes_key

def update_aes_keys(secret_name, secrets):
    client = boto3.client('secretsmanager')
    client.put_secret_value(
        SecretId=secret_name,
        SecretString=json.dumps(secrets)
    )
    logging.info(f"Updated AES keys in {secret_name}")

# Function to instantiate the EncryptionAPI with the AES key fetched from AWS Secrets Manager
def get_encryption_api(contract_idx):
    logging.info(f"Contract to encrypt: {contract_idx}")
    aes_key = get_aes_key(contract_idx)  # Fetch the AES key for this contract
    encryption_key = aes_key.encode()  # Ensure the key is in bytes
    return EncryptionAPI(encryption_key)