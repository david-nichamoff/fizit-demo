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
        del_resp = requests.delete(f'https://api.numbersprotocol.io/api/v3/assets/' + asset["id"], headers=headers)
        if del_resp.status_code == 204:
            print ("Deleted asset " + asset["id"])
        else:
            print ("Request failed with status code:", del_resp.status_code)
else:
    print("Request failed with status code:", response.status_code)
