import requests
import json
import env_var

env_var = env_var.get_env()

# Header information
headers = { 'Authorization' : 'token ' + str(env_var["numbers_key"]) }

# Retrieve all assets
response = requests.get(f'https://api.numbersprotocol.io/api/v3/assets', headers=headers)

if response.status_code == 200:
    response_dict = json.loads(response.text)
    for asset in response_dict["results"]:
        print("ID: " + asset["id"])
        print("Caption: " + asset["caption"])
        print("File size: " + str(asset["asset_file_size"]))
        print("---------------------------")
else:
    print("Request failed with status code:", response.status_code)