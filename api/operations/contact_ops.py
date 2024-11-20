import requests

class ContactOperations:
    def __init__(self, headers, config):
        self.headers = headers
        self.config = config
        self.base_url = f"{self.config['url']}/api/contacts/"

    def add_contact(self, contact_data):
        url = self.base_url
        return requests.post(url, headers=self.headers, json=contact_data)

    def get_contacts(self):
        url = self.base_url
        return requests.get(url, headers=self.headers)

    def delete_contact(self, contact_idx, csrf_token):
        headers_with_csrf = self.headers.copy()
        headers_with_csrf['X-CSRFToken'] = csrf_token

        url = f"{self.base_url}{contact_idx}/"
        return requests.delete(url,
            headers=headers_with_csrf,
            cookies={'csrftoken': csrf_token} 
        )