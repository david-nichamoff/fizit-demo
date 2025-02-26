import requests
import uuid
import logging

from rest_framework.exceptions import ValidationError
from rest_framework import status

from api.secrets import SecretsManager
from api.config import ConfigManager
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import log_error, log_info, log_warning

class ManualAdapter(ResponseMixin):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton instance for ManualAdapter."""
        if cls._instance is None:
            cls._instance = super(ManualAdapter, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def get_accounts(self):
        return []
    def get_recipients(self):
        return []
    def get_deposits(self):
        return []

    def make_payment(self, tx_hash, amount):
        # Simply taxes in a tx_hash and returns it, mimicking other adapters
        return tx_hash
