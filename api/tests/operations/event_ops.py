import requests
from rest_framework import status

class EventOperations:
    def __init__(self, headers, config):
        self.headers = headers
        self.config = config

    def get_events(self, contract_idx, contract_addr):
        response = requests.get(
            f"{self.config['url']}/api/events/",
            headers=self.headers,
            params={"contract_addr": contract_addr, "contract_idx" : contract_idx}
        )
        return response