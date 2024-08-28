import requests
from rest_framework import status

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
            f"{self.config['url']}/api/contracts/{contract_idx}/advances/",
            headers=self.headers
        )
        return response

    def add_advance(self, contract_idx, advances, csrf_token, retries=3, delay=5):
        headers_with_csrf = self.headers.copy()
        headers_with_csrf['X-CSRFToken'] = csrf_token 

        response = requests.post(
            f"{self.config['url']}/api/contracts/{contract_idx}/advances/", 
            headers=headers_with_csrf,
            json=advances,
            cookies={'csrftoken': csrf_token} 
        )

        return response 