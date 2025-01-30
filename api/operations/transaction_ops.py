import requests

class TransactionOperations:
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


    def post_transactions(self, contract_type, contract_idx, transactions):
        batch_size = 10
        url = f"{self.base_url}{contract_type}/{contract_idx}/transactions/"
        headers_with_csrf = self._add_csrf_token()

        count = 0
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i + batch_size]
            response = requests.post(url, json=batch, headers=headers_with_csrf)
            json_response = response.json()

            if "count" not in json_response:
                return self._process_response(response) 

            count += json_response["count"]

        return {"count": count}

    def get_transactions(self, contract_type, contract_idx, transact_min_dt=None, transact_max_dt=None):
        url = f"{self.base_url}{contract_type}/{contract_idx}/transactions/"
        params = {}
        if transact_min_dt:
            params["transact_min_dt"] = transact_min_dt
        if transact_max_dt:
            params["transact_max_dt"] = transact_max_dt

        response = requests.get(url, headers=self.headers, params=params)
        return self._process_response(response)

    def delete_transactions(self, contract_type, contract_idx):
        url = f"{self.base_url}{contract_type}/{contract_idx}/transactions/"
        headers_with_csrf = self._add_csrf_token()
        response = requests.delete(url, headers=headers_with_csrf, cookies={"csrftoken": self.csrf_token})
        return self._process_response(response)

