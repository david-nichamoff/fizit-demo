import requests
import uuid
import logging

from rest_framework.exceptions import ValidationError
from rest_framework import status

from api.managers.app_context import AppContext
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import log_error, log_info, log_warning

class MercuryAdapter(ResponseMixin):

    def __init__(self, context: AppContext):
        self.context = context
        self.secrets_manager = context.secrets_manager
        self.config_manager = context.config_manager
        self.cache_manager = context.cache_manager
        self.account_cache_key = self.cache_manager.get_account_cache_key("mercury")
        self.recipient_cache_key = self.cache_manager.get_recipient_cache_key("mercury")
        self.logger = logging.getLogger(__name__)

    def _build_headers(self):
        """Helper to build request headers."""
        return {"accept": "application/json"}

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
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def get_accounts(self):
        """Fetch accounts from the Mercury API and cache results."""
        cached_accounts = self.cache_manager.get(self.account_cache_key)

        if cached_accounts:
            return cached_accounts

        url = self._build_url('accounts')

        try:
            data = self._send_request('get', url)
            accounts = data.get('accounts', [])

            account_list = [
                {
                    'bank': 'mercury',
                    'account_id': account['id'],
                    'account_name': account['name'],
                    'available_balance': account['availableBalance']
                } for account in accounts
            ]

            # store in Redis cache
            self.cache_manager.set(self.account_cache_key, account_list, timeout=None)
            return account_list

        except Exception as e:
            error_message = f"Error fetching accounts: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def get_recipients(self):
        """Fetch recipients from the Mercury API and cache results."""
        cached_recipients = self.cache_manager.get(self.recipient_cache_key)

        if cached_recipients:
            log_info(self.logger, "Returning cached recipients.")
            return cached_recipients

        url = self._build_url('recipients')

        try:
            data = self._send_request('get', url, headers=self._build_headers())
            recipients = data.get('recipients', [])

            recipient_list = []

            for recipient in recipients:
                routing_info = recipient.get("electronicRoutingInfo") or {}
                address_info = routing_info.get("address") or {}

                log_info(self.logger, f"Routing info: {routing_info}")
                log_info(self.logger, f"Address info: {address_info}")

                recipient_list.append({
                    'bank': 'mercury',
                    'recipient_id': recipient.get('id'),
                    'recipient_name': recipient.get('name'),
                    'payment_method': recipient.get('defaultPaymentMethod'),
                    'account_number': routing_info.get('accountNumber'),
                    'routing_number': routing_info.get('routingNumber'),
                    'bank_name': routing_info.get('bankName'),
                    'address_1': address_info.get('address1'),
                    'address_2': address_info.get('address2'),
                    'city': address_info.get('city'),
                    'region': address_info.get('region'),
                    'postal_code': address_info.get('postalCode'),
                    'country': address_info.get('country')
                })

            self.cache_manager.set(self.recipient_cache_key, recipient_list, timeout=None)
            return recipient_list

        except Exception as e:
            error_message = f"Error fetching recipients: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def get_deposits(self, start_date, end_date, contract):
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
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def make_payment(self, account_id, recipient_id, amount):
        """Initiate a payment to a recipient and clear the cache."""
        log_info(self.logger, f"Attempting payment for account {account_id}, recipient {recipient_id}, amount {amount}")

        url = self._build_url(f"account/{account_id}/request-send-money")
        payload = {
            "recipientId": str(recipient_id),
            "amount": float(amount),
            "paymentMethod": "ach",
            "idempotencyKey": str(uuid.uuid1())
        }
        try:
            response = requests.post(url, auth=(self.secrets_manager.get_mercury_key(), ''), json=payload)

            if response.status_code == status.HTTP_200_OK:
                response_data = response.json()
                tx_hash = response_data.get("requestId", "undefined")
                log_info(self.logger, f"Payment successful: {response_data}, tx_hash: {tx_hash}")
                return tx_hash  # Return transaction hash for storage
            else:
                log_error(self.logger, f"Payment request failed with status {response.status_code}: {response.text}")
                raise RuntimeError(f"Payment failed: {response.text}")

        except Exception as e:
            error_message = f"Error making payment: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def reset_mercury_cache(self):
        self.cache_manager.delete(self.account_cache_key)
        self.cache_manager.delete(self.recipient_cache_key)