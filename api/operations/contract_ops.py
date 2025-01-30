import requests
from rest_framework import status

class ContractOperations:
    def __init__(self, headers, base_url, csrf_token=None):
        self.headers = headers
        self.base_url = base_url
        self.csrf_token = csrf_token

    def _add_csrf_token(self, headers):
        if self.csrf_token:
            headers['X-CSRFToken'] = self.csrf_token
        return headers

    def _process_response(self, response):
        """
        Process the HTTP response:
        - Raise exception for non-2xx status codes.
        - Return parsed JSON data or None.
        """
        return response.json() if response.content else None

    def get_count(self, contract_type):
        response = requests.get(
            f"{self.base_url}/api/contracts/{contract_type}/count/",
            headers=self.headers
        )
        return self._process_response(response)

    def post_contract(self, contract_type, contract_data):
        headers_with_csrf = self._add_csrf_token(self.headers.copy())
        response = requests.post(
            f"{self.base_url}/api/contracts/{contract_type}/",
            json=contract_data,
            headers=headers_with_csrf
        )
        return self._process_response(response)

    def get_contract(self, contract_type, contract_idx):
        response = requests.get(
            f"{self.base_url}/api/contracts/{contract_type}/{contract_idx}/",
            headers=self.headers
        )
        return self._process_response(response)

    def patch_contract(self, contract_type, contract_idx, patch_data):
        headers_with_csrf = self._add_csrf_token(self.headers.copy())
        response = requests.patch(
            f"{self.base_url}/api/contracts/{contract_type}/{contract_idx}/",
            json=patch_data,
            headers=headers_with_csrf
        )
        return self._process_response(response)

    def delete_contract(self, contract_type, contract_idx):
        headers_with_csrf = self._add_csrf_token(self.headers.copy())
        response = requests.delete(
            f"{self.base_url}/api/contracts/{contract_type}/{contract_idx}/",
            headers=headers_with_csrf
        )
        return self._process_response(response)