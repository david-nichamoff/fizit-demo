import json
import logging
from cryptography.fernet import Fernet

from api.secrets import SecretsManager
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning

class Encryptor(ResponseMixin):
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)
        self.logger = logging.getLogger(__name__)

    def encrypt(self, data: dict) -> str:
        json_str = json.dumps(data)
        encrypted_text = self.cipher.encrypt(json_str.encode())
        return encrypted_text.decode()

def get_aes_key_for_encryption():
    """Retrieve the AES key from the loaded secrets for encryption using SecretsManager."""
    secrets_manager = SecretsManager()

    # Get the AES key from the loaded secrets
    aes_key = secrets_manager.get_aes_key()

    if not aes_key:
        raise ValueError("AES key not found in loaded secrets.")

    return aes_key

def get_encryptor():
    """Create an Encryptor instance for encryption."""

    # Get the AES key for encryption
    aes_key = get_aes_key_for_encryption()
    encryption_key = aes_key.encode()  # Ensure the key is in bytes

    return Encryptor(encryption_key)

class Decryptor(ResponseMixin):
    def __init__(self, encryption_key: bytes = None):
        self.logger = logging.getLogger(__name__)
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
                log_warning(self.logger, f"Decryption failed: {e}. Returning 'encrypted data'.")
                return "encrypted data"  # Return 'encrypted data' if decryption fails
        else:
            return "encrypted data"  # Return 'encrypted data' if no key is available

def get_aes_key_for_decryption(api_key: str, parties: list):
    """Retrieve the AES key for decryption using SecretsManager."""
    secrets_manager = SecretsManager()

    # Check for the FIZIT_MASTER_KEY
    master_key = secrets_manager.get_master_key()
    if master_key and api_key == master_key:
        return secrets_manager.get_aes_key()
        
    # Retrieve all partner keys from SecretsManager
    partner_keys = secrets_manager.get_all_partner_keys()

    # Match with party API keys
    for party in parties:
        party_code = party.get("party_code")
        party_api_key = partner_keys.get(party_code)  # Ensure mapping exists

        if party_api_key and party_api_key == api_key:
            return secrets_manager.get_aes_key()  # Return AES key if match found

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