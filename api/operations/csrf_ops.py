import requests
from rest_framework import status

class CsrfOperations:
    def __init__(self, headers, config):
        self.headers = headers
        self.config = config
        self.base_url = f"{self.config['url']}/api/get-csrf-token/"

    def get_csrf_token(self):
        response = requests.get(self.base_url, headers=self.headers)
        if response.status_code == status.HTTP_200_OK:
            return response.cookies['csrftoken']
        else:
            raise RuntimeError(f'Failed to obtain CSRF token. Status code: {response.status_code}\nResponse: {response.content.decode("utf-8")}')