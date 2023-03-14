import requests
import json

url = "https://nwmarketprices.com/api/latest-prices/68/"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    with open('prices_cache.json', 'w') as f:
        json.dump(data, f)
else:
    print(f"Error: {response.status_code}")