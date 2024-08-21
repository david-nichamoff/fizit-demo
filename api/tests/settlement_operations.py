import requests
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta

class SettlementOperations:
    def __init__(self, headers, config):
        self.headers = headers
        self.config = config

    def generate_settlements(self, settle_count, first_due_dt, first_min_dt, first_max_dt):
        settlements = []
        settle_due_dt = datetime.strptime(first_due_dt, "%Y-%m-%d %H:%M:%S")
        transact_min_dt = datetime.strptime(first_min_dt, "%Y-%m-%d %H:%M:%S")
        transact_max_dt = datetime.strptime(first_max_dt, "%Y-%m-%d %H:%M:%S")

        for _ in range(settle_count):
            settlement = {
                "settle_due_dt": settle_due_dt.strftime("%Y-%m-%d"),
                "transact_min_dt": transact_min_dt.strftime("%Y-%m-%d"),
                "transact_max_dt": transact_max_dt.strftime("%Y-%m-%d"),
                "extended_data": {
                    "ref_no": random.randint(1000, 9999)
                }
            }
            settlements.append(settlement)
            settle_due_dt += relativedelta(months=1)
            transact_min_dt += relativedelta(months=1)
            transact_max_dt += relativedelta(months=1)

        return settlements

    def post_settlements(self, contract_idx, settlements):
        response = requests.post(
            f"{self.config['url']}/api/contracts/{contract_idx}/settlements/",
            json=settlements,
            headers=self.headers
        )
        return response

    def get_settlements(self, contract_idx):
        response = requests.get(
            f"{self.config['url']}/api/contracts/{contract_idx}/settlements/",
            headers=self.headers
        )
        return response

    def delete_settlements(self, contract_idx, csrf_token):
        headers_with_csrf = self.headers.copy()
        headers_with_csrf['X-CSRFToken'] = csrf_token

        response = requests.delete(
            f"{self.config['url']}/api/contracts/{contract_idx}/settlements/",
            headers=headers_with_csrf,
            cookies={'csrftoken': csrf_token} 
        )

        return response
