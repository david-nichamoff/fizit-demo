import requests
import uuid
import logging

from rest_framework.exceptions import ValidationError
from rest_framework import status

from api.secrets import SecretsManager
from api.config import ConfigManager
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import log_error, log_info, log_warning

class MercuryAdapter(ResponseMixin):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton instance for MercuryAdapter."""
        if cls._instance is None:
            cls._instance = super(MercuryAdapter, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.secrets_manager = SecretsManager()
            self.config_manager = ConfigManager()
            self.initialized = True
            self.logger = logging.getLogger(__name__)

    def _build_headers(self):
        """Helper to build request headers."""
        return {"accept": "application/json",
                }

    def _build_url(self, endpoint):
        """Helper to construct full API URL."""
        base_url = self.config_manager.get_mercury_url()
        return f"{base_url}/{endpoint}"

    def _send_request(self, method, url, **kwargs):
        """Helper to send an API request."""
        try:
            log_info(self.logger, f"Sending {method.upper()} request to {url} with {kwargs}")

            response = requests.request(method, url, auth=(self.secrets_manager.get_mercury_key(), ''), **kwargs)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            error_message = f"Request failed: {e}"
            log_error(self.logger,  error_message)
            raise RuntimeError(error_message) from e

    def get_accounts(self):
        """Fetch accounts from the Mercury API."""
        url = self._build_url('accounts')
        try:
            data = self._send_request('get', url)
            accounts = data.get('accounts', [])
            return [
                {
                    'bank': 'mercury',
                    'account_id': account['id'],
                    'account_name': account['name'],
                    'available_balance': account['availableBalance']
                } for account in accounts
            ]
        except Exception as e:
            error_message = f"Error fetching accounts: {e}"
            log_warning(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def get_recipients(self):
        """Fetch recipients from the Mercury API."""
        url = self._build_url('recipients')
        try:
            data = self._send_request('get', url, headers=self._build_headers())
            recipients = data.get('recipients', [])
            return [
                {
                    'bank': 'mercury',
                    'recipient_id': recipient['id'],
                    'recipient_name': recipient['name']
                } for recipient in recipients
            ]

        except Exception as e:
            error_message = f"Error fetching recipients: {e}"
            log_error(self.logger,  error_message)
            raise RuntimeError(error_message) from e

    def get_deposits(self, start_date, end_date, contract):
        """Fetch deposits for a specific account within a date range."""
        account_id = contract.get("deposit_instr", {}).get("account_id")

        if not account_id:
            raise ValidationError("Missing deposit_instr.account_id in contract.")

        url = self._build_url(f"account/{account_id}/transactions")
        params = {"start": start_date.strftime('%Y-%m-%d'), "end": end_date.strftime('%Y-%m-%d')}
        try:
            data = self._send_request('get', url, headers=self._build_headers(), params=params)
            transactions = data.get('transactions', [])
            return [
                {
                    'bank': 'mercury',
                    'account_id': account_id,
                    'counterparty': txn['counterpartyName'],
                    'tx_hash': txn['id'],
                    'deposit_amt': txn['amount'],
                    'deposit_dt': txn['createdAt']
                } for txn in transactions if txn['amount'] > 0  # Filter out expenses
            ]
        except ValidationError as e:
            error_message = f"Validation error getting deposits: {e}"
            log_error(self.logger, error_message)
            raise ValidationError(error_message) from e
        except Exception as e:
            error_message = f"Error fetching deposits: {e}"
            log_error(self.logger,  error_message)
            raise RuntimeError(error_message) from e

    def make_payment(self, account_id, recipient_id, amount):
        log_info(self.logger, f"Attempting payment for account {account_id}, recipient {recipient_id}, amount {amount}")

        """Initiate a payment to a recipient."""
        url = self._build_url(f"account/{account_id}/request-send-money")
        payload = {
            "recipientId": str(recipient_id),
            "amount": float(amount),
            "paymentMethod": "ach",
            "idempotencyKey": str(uuid.uuid1())
        }
        try:
            response = requests.post(url, auth=(self.secrets_manager.get_mercury_key(),''), json=payload)

            # Ensure response was successful
            if response.status_code == status.HTTP_200_OK:
                response_data = response.json()
                tx_hash = response_data.get("requestId","undefined")  # Extract transaction ID
                log_info(self.logger, f"Payment successful: {response_data}, tx_hash: {tx_hash}")
                return tx_hash  # Return transaction hash for storage
            else:
                log_error(self.logger, f"Payment request failed with status {response.status_code}: {response.text}")
                raise RuntimeError(f"Payment failed: {response.text}")

        except Exception as e:
            error_message = f"Error making payment: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e