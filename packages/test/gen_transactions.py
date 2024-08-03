import json
import requests
from datetime import datetime, timedelta
import random
import packages.load_keys as load_keys

load_keys = load_keys.get_env()

def get_contracts():
    headers = { 'Authorization': f'Api-Key {load_keys["FIZIT_MASTER_KEY"]}' }
    response = requests.get(load_keys["url"] + "/api/contracts", headers=headers)
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

def delete_transactions(contract_idx):
    url =  load_keys["url"] + f"/api/contracts/{contract_idx}/transactions/"
    headers = { 'Authorization': f'Api-Key {load_keys["FIZIT_MASTER_KEY"]}' }
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        print("Current transactions deleted successfully.")
    else:
        print(f"Failed to delete current transactions. Status code: {response.status_code}")

def prompt_user_for_variables():
    variables = input("Enter the variables (comma-separated): ").split(',')
    variables = [var.strip() for var in variables]
    sample_values = {}
    for var in variables:
        sample_values[var] = float(input(f"Enter a sample value for {var}: "))
    return variables, sample_values

def prompt_user_for_extended_datas():
    extended_data_keys = input("Enter the extended_data keys comma-separated): ").split(',')
    extended_data_keys = [key.strip() for key in extended_data_keys]
    return extended_data_keys

def prompt_user_for_date_range():
    start_date = input("Enter the transaction start date (YYYY-MM-DD): ")
    end_date = input("Enter the transaction end date (YYYY-MM-DD): ")
    return start_date, end_date

def generate_random_time():
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return f"{hour:02}:{minute:02}:{second:02}"

def generate_transactions(contract_idx, variables, sample_values, extended_data_keys, start_date, end_date):
    transactions = []
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    delta = timedelta(days=1)

    current_dt = start_dt
    while current_dt <= end_dt:
        transact_data = {}
        for var in variables:
            value = sample_values[var]
            variance = value * 0.1
            transact_data[var] = round(random.uniform(value - variance, value + variance), 2)

        extended_data = {key: random.randint(1000, 9999) for key in extended_data_keys}

        random_time = generate_random_time()
        transaction = {
            "extended_data": extended_data,
            "transact_dt": f"{current_dt.strftime('%Y-%m-%d')} {random_time}",
            "transact_data": transact_data
        }
        transactions.append(transaction)
        current_dt += delta

    return transactions

def post_transactions(contract_idx, transactions):
    headers = { 'Authorization': f'Api-Key {load_keys["FIZIT_MASTER_KEY"]}' }
    batch_size = 10

    for i in range(0, len(transactions), batch_size):
        batch = transactions[i:i + batch_size]
        response = requests.post(load_keys["url"] + f"/api/contracts/{contract_idx}/transactions/", json=batch, headers=headers)
        if response.status_code == 201:
            print(f"Batch {i//batch_size + 1} of transactions successfully created.")
        else:
            print(f"Failed to create batch {i//batch_size + 1} of transactions. Status code: {response.status_code}")
            print("Response content:", response.content.decode())

def main():
    contracts = get_contracts()
    if not contracts:
        print("No contracts found.")
        return

    selected_contract = prompt_user_for_contract(contracts)
    contract_idx = selected_contract["contract_idx"]

    delete_transactions(contract_idx)
    variables, sample_values = prompt_user_for_variables()
    extended_data_keys = prompt_user_for_extended_datas()
    start_date, end_date = prompt_user_for_date_range()
    transactions = generate_transactions(contract_idx, variables, sample_values, extended_data_keys, start_date, end_date)
    
    # Print transactions as valid JSON for troubleshooting
    print(json.dumps(transactions, indent=4))
    post_transactions(contract_idx, transactions)

if __name__ == "__main__":
    main()