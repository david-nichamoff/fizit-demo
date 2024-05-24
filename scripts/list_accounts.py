import requests

url = "https://api-sandbox.mercury.com/api/v1/accounts"

headers = {
    "accept": "application/json"
}
    
auth = ('secret-token:mercury_sandbox_wma_24QoQiwT4wkYy927qk1shf1FFZD4VDkdWSA2yZg8cZDyJx_yrucrem', '')
response = requests.get(url, headers=headers, auth=auth)

print(response.text)