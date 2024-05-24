import requests
import json

url = "https://api-sandbox.mercury.com/api/v1/accounts"
headers = { "accept" : "application/json" }
auth = ('secret-token:mercury_sandbox_wma_24QoQiwT4wkYy927qk1shf1FFZD4VDkdWSA2yZg8cZDyJx_yrucrem', '')
response = requests.get(url, headers=headers, auth=auth)
accounts = json.loads(response.text)['accounts']

for account in accounts:
    print(account['id'])
    url = f"https://api-sandbox.mercury.com/api/v1/account/{account['id']}/transactions/"
    payload = { 'start' : '2024-01-01'}
    response = requests.get(url, headers=headers, auth=auth, params=payload)
    print (response.text)
    deposits = json.loads(response.text)['transactions']
    for deposit in deposits:
        print (deposit['id'])