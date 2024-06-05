import json
import requests
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import random

import env_var
env_var = env_var.get_env()

def get_contracts():
    headers = { 'Authorization': f'Api-Key {env_var["FIZIT_MASTER_KEY"]}' }
    response = requests.get(env_var["url"] + "/api/contracts", headers=headers)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print(f"Failed to retrieve contracts. Status code: {response.status_code}")
        return []

def prompt_user_for_contract(contracts):
    print("Select a contract to process:")
    for i, contract in enumerate(contracts, 1):
        print(f"{i}. {contract['contract_name']}")
    while True:
        try:
            choice = int(input("Enter the number of the contract: "))
            if 1 <= choice <= len(contracts):
                return contracts[choice - 1]
            else:
                print(f"Please enter a number between 1 and {len(contracts)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def delete_settlements(contract_idx):
    headers = { 'Authorization': f'Api-Key {env_var["FIZIT_MASTER_KEY"]}' }
    response = requests.delete(env_var["url"] + f"/api/contracts/{contract_idx}/settlements/", headers=headers)
    if response.status_code == 204:
        print("Current settlements deleted successfully.")
    else:
        print(f"Failed to delete current settlements. Status code: {response.status_code}")

def prompt_user_for_settlement_params():
    n = int(input("Enter the number of settlement periods: "))
    first_settle_due_dt = input("Enter the first settle_due_dt (YYYY-MM-DD): ")
    first_transact_min_dt = input("Enter the first transact_min_dt (YYYY-MM-DD): ")
    first_transact_max_dt = input("Enter the first transact_max_dt (YYYY-MM-DD): ")
    return n, first_settle_due_dt, first_transact_min_dt, first_transact_max_dt

def generate_settlements(n, first_settle_due_dt, first_transact_min_dt, first_transact_max_dt):
    settlements = []
    settle_due_dt = datetime.strptime(first_settle_due_dt, "%Y-%m-%d")
    transact_min_dt = datetime.strptime(first_transact_min_dt, "%Y-%m-%d")
    transact_max_dt = datetime.strptime(first_transact_max_dt, "%Y-%m-%d")

    for _ in range(n):
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

def post_settlements(contract_idx, settlements):
    headers = { 'Authorization': f'Api-Key {env_var["FIZIT_MASTER_KEY"]}' }
    response = requests.post(env_var["url"] + f"/api/contracts/{contract_idx}/settlements/", json=settlements, headers=headers)
    if response.status_code == 201:
        print("Settlements successfully created.")
    else:
        print(f"Failed to create settlements. Status code: {response.status_code}")

def main():
    contracts = get_contracts()
    if not contracts:
        print("No contracts found.")
        return

    selected_contract = prompt_user_for_contract(contracts)
    contract_idx = selected_contract["contract_idx"]

    delete_settlements(contract_idx)
    n, first_settle_due_dt, first_transact_min_dt, first_transact_max_dt = prompt_user_for_settlement_params()
    settlements = generate_settlements(n, first_settle_due_dt, first_transact_min_dt, first_transact_max_dt)
    print(json.dumps(settlements, indent=4))
    post_settlements(contract_idx, settlements)

if __name__ == "__main__":
    main()