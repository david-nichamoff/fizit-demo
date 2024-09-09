import requests
import uuid
import logging

from api.managers import SecretsManager, ConfigManager

class MercuryAdapter:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure that only one instance of MercuryAdapter is created (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(MercuryAdapter, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            """Initialize the MercuryAPI class with keys and config."""
            self.secrets_manager = SecretsManager()
            self.keys = self.secrets_manager.load_keys()
            self.config_manager = ConfigManager()
            self.config = self.config_manager.load_config()

            self.logger = logging.getLogger(__name__)
            self.initialized = True  # Prevent reinitialization

    def get_accounts(self):
        """Fetch accounts from the Mercury API."""
        try:
            response = requests.get(self.config["mercury_url"] + '/accounts', auth=(self.keys["mercury_token"], ''))
            response.raise_for_status()
            account_data = response.json().get('accounts', [])

            accounts = []
            for account in account_data:
                accounts.append({
                    'bank': 'mercury',
                    'account_id': account['id'],
                    'account_name': account['name'], 
                    'available_balance': account['availableBalance']
                })

            return accounts
        except requests.exceptions.RequestException as e:
            error_message = f"Error fetching accounts: {e}"
            self.logger.error(error_message)
            raise RuntimeError(error_message) from e

    def get_recipients(self):
        """Fetch recipients from the Mercury API."""
        try:
            response = requests.get(self.config["mercury_url"] + '/recipients', auth=(self.keys["mercury_token"], ''))
            response.raise_for_status()
            recipient_data = response.json().get('recipients', [])

            recipients = []
            for recipient in recipient_data:
                recipients.append({
                    'bank': 'mercury',
                    'recipient_id': recipient['id'],
                    'recipient_name': recipient['name']
                })

            return recipients
        except requests.exceptions.RequestException as e:
            error_message = f"Error fetching recipients: {e}"
            self.logger.error(error_message)
            raise RuntimeError(error_message) from e

    def get_deposits(self, start_date, end_date, contract):
        """Fetch deposit transactions for a specific account within a date range."""
        deposits = []
        account_id = contract["funding_instr"]["account_id"]

        url = f"{self.config['mercury_url']}/account/{account_id}/transactions"
        payload = {"start": start_date.strftime('%Y-%m-%d'), "end": end_date.strftime('%Y-%m-%d')}
        headers = {"accept": "application/json"}

        try:
            response = requests.get(url, auth=(self.keys['mercury_token'], ''), headers=headers, params=payload)
            response.raise_for_status()
            deposit_data = response.json().get('transactions', [])

            for deposit in deposit_data:
                if deposit['amount'] > 0:  # filter out expenses
                    deposits.append({
                        'bank': 'mercury', 
                        'account_id': account_id, 
                        'deposit_id': deposit['id'], 
                        'counterparty': deposit['counterpartyName'], 
                        'deposit_amt': deposit['amount'], 
                        'deposit_dt': deposit['createdAt']
                    })

            return deposits
        except requests.exceptions.RequestException as e:
            error_message = f"Error fetching deposits: {e}"
            self.logger.error(error_message)
            raise RuntimeError(error_message) from e

    def make_payment(self, account_id, recipient_id, amount):
        """Initiate a payment to a recipient."""
        idem = str(uuid.uuid1())
        url = f"{self.config['mercury_url']}/account/{account_id}/request-send-money"
        payload = {
            "recipientId": str(recipient_id), 
            "amount": float(amount),
            "paymentMethod": "ach",
            "idempotencyKey": idem
        }

        try:
            response = requests.post(url, auth=(self.keys["mercury_token"], ''), json=payload)
            response.raise_for_status()
            return True, None
        except requests.exceptions.RequestException as e:
            error_message = f"Error making payment: {e}"
            self.logger.error(error_message)
            return False, error_message
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            error_message = e.response.json().get('message') if e.response.headers.get('Content-Type') == 'application/json' else str(e)
            self.logger.error(f"HTTP Error {status_code}: {error_message}")
            return False, f"HTTP Error {status_code}: {error_message}"
        except Exception as e:
            error_message = f"Unexpected Error: {e}"
            self.logger.error(error_message)
            return False, error_message