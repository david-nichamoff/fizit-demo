import requests
from rest_framework import status

class EventOperations:
    def __init__(self, headers, config):
        self.headers = headers
        self.config = config
        self.base_url = f"{self.config['url']}/api/events/"

    def _process_response(self, response):
        """
        Process the HTTP response:
        - Raise exception for non-2xx status codes.
        - Return parsed JSON data or None for empty responses.
        """
        return response.json() if response.content else None

    def get_events(self, contract_idx=None, contract_addr=None):
        """
        Retrieve events filtered by contract_idx and/or contract_addr.
        """
        params = {}
        if contract_idx is not None:
            params["contract_idx"] = contract_idx
        if contract_addr is not None:
            params["contract_addr"] = contract_addr

        response = requests.get(self.base_url, headers=self.headers, params=params)
        return self._process_response(response)