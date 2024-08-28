import requests

class PaymentOperations:
    def __init__(self, headers, config):
        self.headers = headers
        self.config = config

    def get_accounts(self, bank):
        response = requests.get(
            f"{self.config['url']}/api/accounts/",
            headers=self.headers,
            params={"bank": bank}
        )
        return response

    def get_recipients(self, bank):
        response = requests.get(
            f"{self.config['url']}/api/recipients/",
            headers=self.headers,
            params={"bank": bank}
        )
        return response

    def get_advance(self, contract_idx):
        response = requests.get(
            f"{self.config['url']}/api/contracts/{contract_idx}/advance/",
            headers=self.headers
        )
        return response

    def add_advance(self, account_id, amount, currency="USD"):
        payload = {
            "amount": amount,
            "currency": currency
        }
        response = requests.post(
            f"{self.config['url']}/api/accounts/{account_id}/add_advance/",
            headers=self.headers,
            json=payload
        )
        return response
