import requests
import json
import uuid
import logging
import packages.load_keys as load_keys
import packages.load_config as load_config

keys = load_keys.load_keys()
config = load_config.load_config()

logger = logging.getLogger(__name__)

def get_accounts():
    try:
        response = requests.get(config["mercury_url"] + '/accounts', auth=(keys["mercury_token"], ''))
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
        logger.error(error_message)
        raise RuntimeError(error_message) from e

def get_recipients():
    try:
        response = requests.get(config["mercury_url"] + '/recipients', auth=(keys["mercury_token"], ''))
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
        logger.error(error_message)
        raise RuntimeError(error_message) from e

def get_deposits(start_date, end_date, contract):
    deposits = []
    account_id = contract["funding_instr"]["account_id"]

    url = f"{config['mercury_url']}/account/{account_id}/transactions"
    payload = { "start" : start_date.strftime('%Y-%m-%d'), "end" : end_date.strftime('%Y-%m-%d') }
    headers = { "accept" : "application/json" }

    try:
        response = requests.get(url, auth=(keys['mercury_token'],''), headers=headers, params=payload)
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
        logger.error(error_message)
        raise RuntimeError(error_message) from e

def make_payment(account_id, recipient_id, amount):
    idem = str(uuid.uuid1())
    url = f"{config['mercury_url']}/account/{account_id}/request-send-money"
    payload = {
        "recipientId": str(recipient_id), 
        "amount": float(amount),
        "paymentMethod": "ach",
        "idempotencyKey": idem
    }

    try:
        response = requests.post(url, auth=(keys["mercury_token"], ''), json=payload)
        response.raise_for_status()  
        return True, None
    except requests.exceptions.RequestException as e:
        error_message = f"Error making payment: {e}"
        logger.error(error_message)
        return False, error_message
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        error_message = e.response.json().get('message') if e.response.headers.get('Content-Type') == 'application/json' else str(e)
        logger.error(f"HTTP Error {status_code}: {error_message}")
        return False, f"HTTP Error {status_code}: {error_message}"
    except Exception as e:
        error_message = f"Unexpected Error: {e}"
        logger.error(error_message)
        return False, error_message