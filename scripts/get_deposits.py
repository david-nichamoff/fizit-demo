import requests
import json
from datetime import datetime


account_id = "61396d72-e780-11ee-b69b-137ed758771c"
key =  "secret-token:mercury_sandbox_wma_24QoQiwT4wkYy927qk1shf1FFZD4VDkdWSA2yZg8cZDyJx_yrucrem"

url = f"https://api-sandbox.mercury.com/api/v1/account/{account_id}/transactions"
print(url)
payload = { "start" : '2024-01-01', "end" : '2024-06-03' }

headers= {
    "accept" : "application/json"
}

now = datetime.now()
print("Current Time:", now.strftime("%H:%M:%S"))

response = requests.get(url, auth=(key,''), headers=headers, params=payload)
print(response.text)

if response.status_code != 404:
    deposit_data = json.loads(response.text)["transactions"]
    for deposit in deposit_data:
        print(deposit["id"])