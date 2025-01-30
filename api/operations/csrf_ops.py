import requests
from rest_framework import status

class CsrfOperations:
    def __init__(self, headers, base_url):
        self.headers = headers
        self.base_url = f"{base_url}/api/get-csrf-token/"

    def get_csrf_token(self):
        response = requests.get(self.base_url, headers=self.headers)
        if response.status_code == status.HTTP_200_OK:
            return response.cookies['csrftoken']
        else:
            raise RuntimeError(f'Failed to obtain CSRF token. Status code: {response.status_code}\nResponse: {response.content.decode("utf-8")}')