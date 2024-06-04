import requests
import json
import env_var
import uuid

env_var = env_var.get_env()

def get_accounts():
    try:
        response = requests.get(env_var["mercury_url"] + '/accounts', auth=(env_var["mercury_token"], ''))
        response.raise_for_status()
        account_data = json.loads(response.text)['accounts']

        accounts = []
        for account in account_data:
            accounts.append({'bank' : 'mercury', 'account_id': account['id'], 'account_name' : account['name'], 
                             'available_balance' : account['availableBalance']})
        return accounts
    except requests.exceptions.RequestException as e:
        print(f"Error fetching accounts: {e}")
        return []

def get_recipients():
    try:
        response = requests.get(env_var["mercury_url"] + '/recipients', auth=(env_var["mercury_token"], ''))
        response.raise_for_status()
        recipient_data = json.loads(response.text)['recipients']

        recipients = []
        for recipient in recipient_data:
            recipients.append({'bank' : 'mercury', 'recipient_id':recipient['id'],'recipient_name':recipient['name']})
        return recipients
    except requests.exceptions.RequestException as e:
        print(f"Error fetching recipients: {e}")
        return []

def get_deposits(start_date, end_date, account_id):
    deposits = []
    url = f"{env_var["mercury_url"]}/account/{account_id}/transactions"
    payload = { "start" : start_date.strftime('%Y-%m-%d'), "end" : end_date.strftime('%Y-%m-%d') }
    headers = { "accept" : "application/json" }

    try:
        response = requests.get(url, auth=(env_var['mercury_token'],''), headers=headers, params=payload)
        deposit_data = json.loads(response.text)['transactions']

        for deposit in deposit_data:
            if deposit['amount'] > 0:  # filter out expenses
                deposits.append({'bank' : 'mercury', 'account_id': account_id, 
                    'deposit_id' : deposit['id'], 'counterparty' : deposit['counterpartyName'], 
                    'deposit_amt' : deposit['amount'], 'deposit_dt' : deposit['createdAt']})
    except requests.exceptions.RequestException as e:
        print(f"Error fetching deposit: {e}")

    return deposits

def make_payment(account_id, recipient_id, amount):
    idem = str(uuid.uuid1())
    url = f"{env_var["mercury_url"]}/account/{account_id}/request-send-money"
    payload = { "recipientId" : recipient_id, "amount" : float(amount), "paymentMethod" : "ach", "idempotencyKey" : idem }

    try:
        response = requests.post(url, auth=(env_var["mercury_token"], ''), json=payload)
        response.raise_for_status()
        return True, None
    except requests.exceptions.RequestException as e:
        return False, f"Error: {e}"
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        error_message = e.response.json().get('message') if e.response.headers['Content-Type'] == 'application/json' else str(e)
        return False, f"HTTP Error {status_code}: {error_message}"
    except Exception as e:
        return False, f"Unexpected Error: {e}"
