#!/usr/bin/env python3
"""Quick test to trigger Set Action and check logs"""

import requests
import json
import time

# Set Action request
url = 'http://localhost:8080/proxy_fetch'
payload = {
    'url': 'https://httpbin.org/post',  # Test endpoint
    'token': 'test-token',
    'isPost': True,
    'postData': {
        'action': 'Trans-Begin',
        'cids': ['cust1', 'cust2']
    },
    'contentType': 'application/json'
}

print("Sending Set Action request...")
print(json.dumps(payload, indent=2))

try:
    response = requests.post(url, json=payload, timeout=5)
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

print("\nCheck Flask logs for [DEBUG] and [SET_ACTION] messages")
