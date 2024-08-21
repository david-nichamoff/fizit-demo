import requests
import time
from rest_framework import status

class PartyOperations:
    def __init__(self, headers, config):
        self.headers = headers
        self.config = config

    def add_parties(self, contract_idx, parties_data):
        response = requests.post(
            f"{self.config['url']}/api/contracts/{contract_idx}/parties/",
            json=parties_data,
            headers=self.headers
        )
        return response

    def get_parties(self, contract_idx):
        response = requests.get(
            f"{self.config['url']}/api/contracts/{contract_idx}/parties/",
            headers=self.headers
        )
        return response

    def delete_party(self, contract_idx, party_idx, csrf_token, retries=3, delay=5):
        headers_with_csrf = self.headers.copy()
        headers_with_csrf['X-CSRFToken'] = csrf_token

        for attempt in range(retries):
            delete_url = f"{self.config['url']}/api/contracts/{contract_idx}/parties/{party_idx}"
            response = requests.delete(
                delete_url,
                headers=headers_with_csrf,
                cookies={'csrftoken': csrf_token} 
            )

            if response.status_code == status.HTTP_204_NO_CONTENT:
                return response
            else:
                print(f"Attempt {attempt + 1} failed with status code {response.status_code}. Retrying in {delay} seconds...")
                time.sleep(delay)

        return response

    def delete_parties(self, contract_idx, csrf_token, retries=3, delay=5):
        headers_with_csrf = self.headers.copy()
        headers_with_csrf['X-CSRFToken'] = csrf_token 

        response = requests.delete(
            f"{self.config['url']}/api/contracts/{contract_idx}/parties/", 
            headers=headers_with_csrf,
            cookies={'csrftoken': csrf_token} 
        )

        return response