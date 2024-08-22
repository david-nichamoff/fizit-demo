import requests

class BankOperations:
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

    def get_deposits(self, bank):
        response = requests.get(
            f"{self.config['url']}/api/deposits/",
            headers=self.headers,
            params={"bank": bank}
        )
        return response

    def pay_advance(self, account_id, amount, currency="USD"):
        payload = {
            "amount": amount,
            "currency": currency
        }
        response = requests.post(
            f"{self.config['url']}/api/accounts/{account_id}/pay_advance/",
            headers=self.headers,
            json=payload
        )
        return response
