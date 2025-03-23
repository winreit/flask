import requests


response = requests.get(
    "http://127.0.0.1:5000/owner/1",
)
print(response.json())