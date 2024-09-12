import requests

class BankOperations:
    def __init__(self, headers, config):
        self.headers = headers
        self.config = config

    def get_accounts(self, bank):
        response = requests.get(
            f"{self.config['url']}/api/accounts/",
            headers=self.headers,
            params={"bank": bank}
        )
        return response

    def get_recipients(self, bank):
        response = requests.get(
            f"{self.config['url']}/api/recipients/",
            headers=self.headers,
            params={"bank": bank}
        )
        return response

    def get_advances(self, contract_idx):
        response = requests.get(
            f"{self.config['url']}/api/contracts/{contract_idx}/advances/",
            headers=self.headers
        )
        return response

    def add_advances(self, contract_idx, advances, csrf_token):
        headers_with_csrf = self.headers.copy()
        headers_with_csrf['X-CSRFToken'] = csrf_token 

        response = requests.post(
            f"{self.config['url']}/api/contracts/{contract_idx}/advances/", 
            headers=headers_with_csrf,
            json=advances,
            cookies={'csrftoken': csrf_token} 
        )
        
        return response
    
    def get_deposits(self, contract_idx, start_date, end_date):
        response = requests.get(
            f"{self.config['url']}/api/contracts/{contract_idx}/deposits/",
            headers=self.headers,
            params={"start_date": start_date, "end_date": end_date}
        )
        return response

    def add_deposits(self, contract_idx, deposits, csrf_token, retries=3, delay=5):
        headers_with_csrf = self.headers.copy()
        headers_with_csrf['X-CSRFToken'] = csrf_token 

        response = requests.post(
            f"{self.config['url']}/api/contracts/{contract_idx}/deposits/", 
            headers=headers_with_csrf,
            json=deposits,
            cookies={'csrftoken': csrf_token} 
        )
        
        return response

    def get_residuals(self, contract_idx):
        response = requests.get(
            f"{self.config['url']}/api/contracts/{contract_idx}/residuals/",
            headers=self.headers
        )
        return response

    def add_residuals(self, contract_idx, residuals, csrf_token, retries=3, delay=5):
        headers_with_csrf = self.headers.copy()
        headers_with_csrf['X-CSRFToken'] = csrf_token 

        response = requests.post(
            f"{self.config['url']}/api/contracts/{contract_idx}/residuals/", 
            headers=headers_with_csrf,
            json=residuals,
            cookies={'csrftoken': csrf_token} 
        )
        return response
