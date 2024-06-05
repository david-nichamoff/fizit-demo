import json
import os
import requests
from datetime import datetime

import env_var
env_var = env_var.get_env()

def contract_exists(contracts, contract_name):
    for contract in contracts:
        if contract["contract_name"] == contract_name:
            return contract["contract_idx"]
    return -1

def get_json_files():
    return [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.json')]

def prompt_user_for_file(json_files):
    print("Select a file to process:")
    for i, file in enumerate(json_files, 1):
        print(f"{i}. {file}")
    while True:
        try:
            choice = int(input("Enter the number of the file: "))
            if 1 <= choice <= len(json_files):
                return json_files[choice - 1]
            else:
                print(f"Please enter a number between 1 and {len(json_files)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def partial_update(contract_data, contract_idx):
    headers = { 'Authorization': f'Api-Key {env_var["FIZIT_MASTER_KEY"]}' }
    response = requests.patch(env_var["url"] + f'/api/contracts/{contract_idx}/', json=contract_data, headers=headers)
    return response

def create_contract(contract_data):
    headers = { 'Authorization': f'Api-Key {env_var["FIZIT_MASTER_KEY"]}' }
    response = requests.post(env_var["url"] + '/api/contracts/', json=contract_data, headers=headers)
    return response

def main():
    json_files = get_json_files()
    if not json_files:
        print("No JSON files found in the current directory.")
        return

    contract_file = prompt_user_for_file(json_files)
    with open(contract_file, 'r') as file:
        contract_data = json.load(file)

    contract_name = contract_data.get("contract_name")
    if not contract_name:
        print("The selected JSON file does not contain a 'contract_name' key.")
        return

    headers = { 'Authorization': f'Api-Key {env_var["FIZIT_MASTER_KEY"]}' }
    response = requests.get(env_var["url"] + 'api/contracts', headers=headers)
    contracts = json.loads(response.text)
    contract_idx = contract_exists(contracts, contract_name)

    if contract_idx >= 0:
        response = partial_update(contract_data, contract_idx)
        if response.status_code == 200:
            print(f"Contract '{contract_name}' successfully updated.")
        else:
            print(f"Failed to update contract '{contract_name}'. Status code: {response.status_code}")
    else:
        response = create_contract(contract_data)
        if response.status_code == 201:
            print(f"Contract '{contract_name}' successfully created.")
        else:
            print(f"Failed to create contract '{contract_name}'. Status code: {response.status_code}")

if __name__ == "__main__":
    main()