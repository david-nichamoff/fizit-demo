import requests

class ContactOperations:
    def __init__(self, headers, config, csrf_token=None):
        self.headers = headers
        self.config = config
        self.csrf_token = csrf_token
        self.base_url = f"{self.config['url']}/api/contacts/"

    def _add_csrf_token(self, headers):
        """Add CSRF token to headers if available."""
        if self.csrf_token:
            headers['X-CSRFToken'] = self.csrf_token
        return headers

    def _process_response(self, response):
        """
        Process the HTTP response:
        - Raise exception for non-2xx status codes.
        - Return parsed JSON data or None for empty responses.
        """
        return response.json() if response.content else None

    def post_contact(self, contact_data):
        """Create a new contact."""
        url = self.base_url
        response = requests.post(url, headers=self.headers, json=contact_data)
        return self._process_response(response)

    def get_contacts(self):
        """Retrieve all contacts."""
        url = self.base_url
        response = requests.get(url, headers=self.headers)
        return self._process_response(response)

    def delete_contact(self, contact_idx):
        """Delete a specific contact by ID."""
        headers_with_csrf = self._add_csrf_token(self.headers.copy())
        url = f"{self.base_url}{contact_idx}/"
        response = requests.delete(
            url,
            headers=headers_with_csrf,
            cookies={'csrftoken': self.csrf_token}
        )
        return self._process_response(response)