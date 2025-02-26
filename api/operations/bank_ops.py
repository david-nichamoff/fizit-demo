import requests

class BankOperations:
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
        - Raise exception for non-2xx status codes.
        - Return parsed JSON data or None.
        """
        return response.json() if response.content else None

    def get_accounts(self, bank):
        """Retrieve bank accounts."""
        response = requests.get(
            f"{self.base_url}/api/accounts/",
            headers=self.headers,
            params={"bank": bank}
        )
        return self._process_response(response)

    def get_recipients(self, bank):
        """Retrieve recipients for a specific bank."""
        response = requests.get(
            f"{self.base_url}/api/recipients/",
            headers=self.headers,
            params={"bank": bank}
        )
        return self._process_response(response)

    def get_advances(self, contract_type, contract_idx):
        """Retrieve advances for a contract."""
        response = requests.get(
            f"{self.base_url}/api/contracts/{contract_type}/{contract_idx}/advances/",
            headers=self.headers
        )
        return self._process_response(response)

    def post_advances(self, contract_type, contract_idx, advances):
        """Add advances for a contract."""
        headers_with_csrf = self._add_csrf_token(self.headers.copy())
        response = requests.post(
            f"{self.base_url}/api/contracts/{contract_type}/{contract_idx}/advances/",
            headers=headers_with_csrf,
            json=advances,
            cookies={'csrftoken': self.csrf_token}
        )
        return self._process_response(response)

    def get_deposits(self, contract_type, contract_idx, start_date, end_date):
        """Retrieve deposits for a contract within a date range."""
        response = requests.get(
            f"{self.base_url}/api/contracts/{contract_type}/{contract_idx}/deposits/",
            headers=self.headers,
            params={"start_date": start_date, "end_date": end_date}
        )
        return self._process_response(response)

    def post_deposit(self, contract_type, contract_idx, deposit):
        """Add deposits to a contract."""
        headers_with_csrf = self._add_csrf_token(self.headers.copy())
        response = requests.post(
            f"{self.base_url}/api/contracts/{contract_type}/{contract_idx}/deposits/",
            headers=headers_with_csrf,
            json=deposit,
            cookies={'csrftoken': self.csrf_token}
        )
        return self._process_response(response)

    def get_residuals(self, contract_type, contract_idx):
        """Retrieve residuals for a contract."""
        response = requests.get(
            f"{self.base_url}/api/contracts/{contract_type}/{contract_idx}/residuals/",
            headers=self.headers
        )
        return self._process_response(response)

    def post_residuals(self, contract_type, contract_idx, residuals):
        """Add residuals for a contract."""
        headers_with_csrf = self._add_csrf_token(self.headers.copy())
        response = requests.post(
            f"{self.base_url}/api/contracts/{contract_type}/{contract_idx}/residuals/",
            headers=headers_with_csrf,
            json=residuals,
            cookies={'csrftoken': self.csrf_token}
        )
        return self._process_response(response)

    def get_distributions(self, contract_type, contract_idx):
        """Retrieve distributions for a contract."""
        response = requests.get(
            f"{self.base_url}/api/contracts/{contract_type}/{contract_idx}/distributions/",
            headers=self.headers
        )
        return self._process_response(response)

    def post_distributions(self, contract_type, contract_idx, distributions):
        """Add residuals for a contract."""
        headers_with_csrf = self._add_csrf_token(self.headers.copy())
        response = requests.post(
            f"{self.base_url}/api/contracts/{contract_type}/{contract_idx}/distributions/",
            headers=headers_with_csrf,
            json=distributions,
            cookies={'csrftoken': self.csrf_token}
        )
        return self._process_response(response)