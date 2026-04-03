import logging
import os
import sys

import requests


logging.basicConfig(level=logging.INFO)


repository = os.environ["GITHUB_REPOSITORY"]
q_repo = os.environ["Q_REPO"]

url = f"https://api.github.com/repos/{q_repo}/dispatches"
token = os.environ['TOKEN']
image_url = os.environ['IMAGE_URL']
ai_model = os.environ.get('AI_MODEL', '')

logging.info(f"Dispatching to {url}")


# Headers
headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}",
}

# Payload
payload = {
    "event_type": "test dispatch",
    "client_payload": {
        "repository": repository,
        "image_url": image_url,
        "ai_model": ai_model,
    },
}

# Send the request
response = requests.post(url, headers=headers, json=payload)

assert response.ok, response.text

# Check result
if response.status_code == 204:
    print("Dispatch succeeded!")
else:
    print(f"Dispatch failed with status {response.status_code}: {response.text}")
    sys.exit(1)  # Fail the workflow
