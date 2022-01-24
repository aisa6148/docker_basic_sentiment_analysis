from __future__ import print_function
import requests
import sys

def client(endpoint):
    headers = {'content-type': 'application/json'}
    response = requests.get(endpoint, headers=headers)
    print("Response is", response)
    print(response.text)

host = sys.argv[1]

endpoint = f"http://{host}:5001/"

client(endpoint)
print(f"Running against {endpoint}")