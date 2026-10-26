import json
import requests

url = "http://127.0.0.1:8000/api/search"
payload = {"query": "person", "topK": 5}

res = requests.post(url, json=payload)
print(f"Status Code: {res.status_code}")
print(json.dumps(res.json(), indent=2))
