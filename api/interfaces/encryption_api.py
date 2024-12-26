import json
import logging
from cryptography.fernet import Fernet
from api.managers import SecretsManager

class Encryptor:
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)

    def encrypt(self, data: dict) -> str:
        json_str = json.dumps(data)
        encrypted_text = self.cipher.encrypt(json_str.encode())
        return encrypted_text.decode()

def get_aes_key_for_encryption():
    """Retrieve the AES key from the loaded secrets for encryption using SecretsManager."""
    secrets_manager = SecretsManager()
    keys = secrets_manager.load_keys()

    # Get the AES key from the loaded secrets
    aes_key = keys.get('aes_key')

    if not aes_key:
        raise ValueError("AES key not found in loaded secrets.")

    logging.info("Retrieved AES key for encryption from secrets manager")
    return aes_key

def get_encryptor():
    """Create an Encryptor instance for encryption."""
    logging.info("Fetching AES key from SecretsManager for encryption")
    
    # Get the AES key for encryption
    aes_key = get_aes_key_for_encryption()
    encryption_key = aes_key.encode()  # Ensure the key is in bytes

    return Encryptor(encryption_key)

class Decryptor:
    def __init__(self, encryption_key: bytes = None):
        if encryption_key:
            self.cipher = Fernet(encryption_key)
        else:
            self.cipher = None  # No decryption will be done if no key is provided

    def decrypt(self, encrypted_text: str) -> str:
        if self.cipher:
            try:
                decrypted_text = self.cipher.decrypt(encrypted_text.encode()).decode()
                return json.loads(decrypted_text)
            except Exception as e:
                logging.warning(f"Decryption failed: {e}. Returning 'encrypted data'.")
                return "encrypted data"  # Return 'encrypted data' if decryption fails
        else:
            return "encrypted data"  # Return 'encrypted data' if no key is available

def get_aes_key_for_decryption(api_key: str, parties: list):
    """Retrieve the AES key for decryption using SecretsManager."""
    secrets_manager = SecretsManager()
    keys = secrets_manager.load_keys()

    # Check for the FIZIT_MASTER_KEY
    master_key = keys.get('FIZIT_MASTER_KEY')
    if master_key and api_key == master_key:
        return keys.get('aes_key')

    # Match with party API keys
    for party in parties:
        party_key = keys.get(party['party_code'])
        if party_key == api_key:
            return keys.get('aes_key')

    # If no match is found, return None (this will signal to return 'encrypted data')
    return None

def get_decryptor(api_key: str, parties: list):
    """Create a Decryptor instance for decryption."""

    # Get the AES key for decryption
    aes_key = get_aes_key_for_decryption(api_key, parties)
    
    if aes_key:
        decryption_key = aes_key.encode()  # Ensure the key is in bytes
        return Decryptor(decryption_key)
    else:
        return Decryptor()  # No key provided, return 'encrypted data'