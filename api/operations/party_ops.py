import logging
import requests
import time
import json

from rest_framework import status

from api.utilities.logging import log_error, log_info, log_warning

logger = logging.getLogger(__name__)

class PartyOperations:
    def __init__(self, headers, base_url, csrf_token=None):
        self.headers = headers
        self.base_url = base_url 
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

    def post_parties(self, contract_type, contract_idx, parties_data):
        """
        Add parties to a contract.
        """
        headers_with_csrf = self._add_csrf_token(self.headers.copy())
        response = requests.post(
            f"{self.base_url}/api/contracts/{contract_type}/{contract_idx}/parties/",
            json=parties_data,
            headers=headers_with_csrf
        )
        return self._process_response(response)

    def approve_party(self, contract_type, contract_idx, party_idx, approved_user):
        """
        Add an approval to a contract
        """
        headers_with_csrf = self._add_csrf_token(self.headers.copy())
        payload = {
            "approved_user": approved_user
        }

        response = requests.post(
            f"{self.base_url}/api/contracts/{contract_type}/{contract_idx}/{party_idx}/approve/",
            json=payload,
            headers=headers_with_csrf
        )
        return self._process_response(response)

    def get_parties(self, contract_type, contract_idx):
        """
        Retrieve all parties for a specific contract.
        """
        response = requests.get(
            f"{self.base_url}/api/contracts/{contract_type}/{contract_idx}/parties/",
            headers=self.headers
        )
        return self._process_response(response)

    def delete_parties(self, contract_type, contract_idx):
        """
        Delete all parties from a specific contract.
        """
        headers_with_csrf = self._add_csrf_token(self.headers.copy())
        response = requests.delete(
            f"{self.base_url}/api/contracts/{contract_type}/{contract_idx}/parties/",
            headers=headers_with_csrf,
            cookies={'csrftoken': self.csrf_token}
        )
        return self._process_response(response)
