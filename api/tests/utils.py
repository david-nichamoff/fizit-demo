import requests
import random
from rest_framework import status

import packages.load_config as load_config
config = load_config.load_config()

class Utils:
    def __init__(self, headers, config):
        self.headers = headers
        self.config = config

    def _get_csrf_token(self):
        response = requests.get(f"{config['url']}/api/get-csrf-token/", headers=self.headers)
        if response.status_code == status.HTTP_200_OK:
            return response.cookies['csrftoken']
        else:
            self.fail(f'Failed to obtain CSRF token. Status code: {response.status_code}\nResponse: {response.content.decode("utf-8")}')