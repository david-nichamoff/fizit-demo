import requests

class SettlementOperations:
    def __init__(self, headers, base_url, csrf_token=None):
        self.headers = headers
        self.csrf_token = csrf_token
        self.base_url = f"{base_url}/api/contracts/"

    def _add_csrf_token(self):
        """Add CSRF token to headers if required."""
        if not self.csrf_token:
            raise ValueError("CSRF token is required for this operation.")
        headers_with_csrf = self.headers.copy()
        headers_with_csrf["X-CSRFToken"] = self.csrf_token
        return headers_with_csrf

    def _process_response(self, response):
        """
        Process the HTTP response:
        - Raise an exception for non-2xx status codes.
        - Return parsed JSON data or None for empty responses.
        """
        return response.json() if response.content else None

    def post_settlements(self, contract_type, contract_idx, settlements):
        url = f"{self.base_url}{contract_type}/{contract_idx}/settlements/"
        headers_with_csrf = self._add_csrf_token()
        response = requests.post(url, json=settlements, headers=headers_with_csrf)
        return self._process_response(response)

    def get_settlements(self, contract_type, contract_idx):
        url = f"{self.base_url}{contract_type}/{contract_idx}/settlements/"
        response = requests.get(url, headers=self.headers)
        return self._process_response(response)

    def delete_settlements(self, contract_type, contract_idx):
        url = f"{self.base_url}{contract_type}/{contract_idx}/settlements/"
        headers_with_csrf = self._add_csrf_token()
        response = requests.delete(url, headers=headers_with_csrf, cookies={"csrftoken": self.csrf_token})
        return self._process_response(response)