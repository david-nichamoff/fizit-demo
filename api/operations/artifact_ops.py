import requests

class ArtifactOperations:
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
        - Return parsed JSON data or None.
        """
        return response.json() if response.content else None

    def get_artifacts(self, contract_type, contract_idx):
        """Retrieve all artifacts associated with a contract."""
        response = requests.get(
            f"{self.base_url}/api/contracts/{contract_type}/{contract_idx}/artifacts/",
            headers=self.headers
        )
        return self._process_response(response)

    def post_artifacts(self, contract_type, contract_idx, artifact_urls):
        """Add artifacts to a contract using their URLs."""
        headers_with_csrf = self._add_csrf_token(self.headers.copy())
        response = requests.post(
            f"{self.base_url}/api/contracts/{contract_type}/{contract_idx}/artifacts/",
            headers=headers_with_csrf,
            json=artifact_urls,
            cookies={'csrftoken': self.csrf_token}
        )
        return self._process_response(response)

    def delete_artifacts(self, contract_type, contract_idx):
        """Delete all artifacts associated with a contract."""
        headers_with_csrf = self._add_csrf_token(self.headers.copy())
        response = requests.delete(
            f"{self.base_url}/api/contracts/{contract_type}/{contract_idx}/artifacts/",
            headers=headers_with_csrf,
            cookies={'csrftoken': self.csrf_token}
        )
        return self._process_response(response)