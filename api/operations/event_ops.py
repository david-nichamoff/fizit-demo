import requests
import logging
from rest_framework import status

from api.utilities.logging import log_info, log_warning, log_error

class EventOperations:
    def __init__(self, headers, base_url, csrf_token=None):
        self.headers = headers
        self.base_url = base_url
        self.csrf_token = csrf_token
        self.logger = logging.getLogger(__name__)

    def _add_csrf_token(self, headers):
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

    def get_events(self, contract_type=None, contract_idx=None):
        """
        Retrieve events filtered by contract_idx and/or contract_type.
        """
        params = {}
        if contract_type is not None:
            params["contract_type"] = contract_type
        if contract_idx is not None:
            params["contract_idx"] = contract_idx

        url = f"{self.base_url}/api/events/"

        log_info(self.logger, f"Making request to events API at {url} with params: {params}")

        response = requests.get(url, headers=self.headers, params=params)

        log_info(self.logger, f"Response status code: {response.status_code}")
        log_info(self.logger, f"Response content: {response.content}")

        return self._process_response(response)