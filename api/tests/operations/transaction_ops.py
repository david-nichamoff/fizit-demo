import requests
import random

from datetime import datetime, timedelta

from rest_framework import status

class TransactionOperations:
    def __init__(self, headers, config):
        self.headers = headers
        self.config = config

    def generate_transactions(self, contract_idx, variables, sample_values, extended_data_keys, start_date, end_date):
        start_dt = datetime.strptime(start_date.split()[0], "%Y-%m-%d")  # Only take the date part
        end_dt = datetime.strptime(end_date.split()[0], "%Y-%m-%d") - timedelta(days=1)  # Adjust end_date to the day before

        transactions = []
        delta = timedelta(days=1)

        current_dt = start_dt
        while current_dt <= end_dt:
            transact_data = {}
            for var in variables:
                value = sample_values[var]
                variance = value * 0.1

                # Convert Decimal values to float for random.uniform
                min_value = value - variance
                max_value = value + variance
                transact_data[var] = round(random.uniform(min_value, max_value), 2)

            extended_data = {key: random.randint(1000, 9999) for key in extended_data_keys}

            random_time = self._generate_random_time()
            transaction_dt = f"{current_dt.strftime('%Y-%m-%d')} {random_time}"
            transaction = {
                "extended_data": extended_data,
                "transact_dt": datetime.strptime(transaction_dt, '%Y-%m-%d %H:%M:%S').isoformat(),  # Format datetime correctly
                "transact_data": transact_data
            }
            transactions.append(transaction)
            current_dt += delta

        return transactions

    def post_transactions(self, contract_idx, transactions):
        batch_size = 10
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i + batch_size]
            response = requests.post(f"{self.config['url']}/api/contracts/{contract_idx}/transactions/", json=batch, headers=self.headers)
            if response.status_code != status.HTTP_201_CREATED:
                return response
        return response

    def get_transactions(self, contract_idx, transact_min_dt=None, transact_max_dt=None):
        params = {}

        # Just pass the dates as-is without converting
        if transact_min_dt:
            params['transact_min_dt'] = transact_min_dt  # Assume it's already in ISO 8601 format

        if transact_max_dt:
            params['transact_max_dt'] = transact_max_dt  # Assume it's already in ISO 8601 format

        response = requests.get(
            f"{self.config['url']}/api/contracts/{contract_idx}/transactions/",
            headers=self.headers,
            params=params
        )
        return response

    def delete_transactions(self, contract_idx, csrf_token):
        headers_with_csrf = self.headers.copy()
        headers_with_csrf['X-CSRFToken'] = csrf_token 

        response = requests.delete(
            f"{self.config['url']}/api/contracts/{contract_idx}/transactions/", 
            headers=headers_with_csrf,
            cookies={'csrftoken': csrf_token} 
        )

        return response

    def _generate_random_time(self):
        return f"{random.randint(0, 23):02}:{random.randint(0, 59):02}:{random.randint(0, 59):02}"
