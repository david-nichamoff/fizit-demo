import requests
import time
from rest_framework import status


class PartyOperations:
    def __init__(self, headers, config, csrf_token=None):
        self.headers = headers
        self.config = config
        self.csrf_token = csrf_token

    def _add_csrf_token(self, headers):
        """Add CSRF token to headers if available."""
        if self.csrf_token:
            headers['X-CSRFToken'] = self.csrf_token
        return headers

    def _process_response(self, response):
        """
        Process the HTTP response:
        - Raise an exception for non-2xx status codes.
        - Return parsed JSON data or None for empty responses.
        """
        return response.json() if response.content else None

    def post_parties(self, contract_idx, parties_data):
        """
        Add parties to a contract.
        """
        headers_with_csrf = self._add_csrf_token(self.headers.copy())
        response = requests.post(
            f"{self.config['url']}/api/contracts/{contract_idx}/parties/",
            json=parties_data,
            headers=headers_with_csrf
        )
        return self._process_response(response)

    def get_parties(self, contract_idx):
        """
        Retrieve all parties for a specific contract.
        """
        response = requests.get(
            f"{self.config['url']}/api/contracts/{contract_idx}/parties/",
            headers=self.headers
        )
        return self._process_response(response)

    def delete_party(self, contract_idx, party_idx):
        """
        Delete a specific party from a contract with retry logic.
        """
        headers_with_csrf = self._add_csrf_token(self.headers.copy())
        delete_url = f"{self.config['url']}/api/contracts/{contract_idx}/parties/{party_idx}/"

        response = requests.delete(
            delete_url,
            headers=headers_with_csrf,
            cookies={'csrftoken': self.csrf_token}
        )
        return self._process_response(response)

    def delete_parties(self, contract_idx):
        """
        Delete all parties from a specific contract.
        """
        headers_with_csrf = self._add_csrf_token(self.headers.copy())
        response = requests.delete(
            f"{self.config['url']}/api/contracts/{contract_idx}/parties/",
            headers=headers_with_csrf,
            cookies={'csrftoken': self.csrf_token}
        )
        return self._process_response(response)