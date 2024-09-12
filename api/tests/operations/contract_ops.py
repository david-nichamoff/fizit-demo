import requests

class ContractOperations:
    def __init__(self, headers, config):
        self.headers = headers
        self.config = config

    def load_contract(self, contract_data):
        response = requests.post(
            f"{self.config['url']}/api/contracts/",
            json=contract_data,
            headers=self.headers
        )
        return response

    def get_contract(self, contract_idx):
        response = requests.get(
            f"{self.config['url']}/api/contracts/{contract_idx}/",
            headers=self.headers
        )
        return response

    def patch_contract(self, contract_idx, patch_data):
        response = requests.patch(
            f"{self.config['url']}/api/contracts/{contract_idx}/",
            json=patch_data,
            headers=self.headers
        )
        return response

    def delete_contract(self, contract_idx):
        response = requests.delete(
            f"{self.config['url']}/api/contracts/{contract_idx}/",
            headers=self.headers
        )
        return response