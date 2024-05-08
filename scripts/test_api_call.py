import requests

url = 'http://127.0.0.1:8000/api/contracts/'
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f"Request failed with status code: {response.status_code}")
