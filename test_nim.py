import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('NVIDIA_API_KEY')

print("Testing NIM connectivity with meta/llama-3.1-8b-instruct")

try:
    response = requests.post(
        'https://integrate.api.nvidia.com/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        json={'model': 'meta/llama-3.1-8b-instruct', 'messages': [{'role': 'user', 'content': 'hi'}], 'max_tokens': 10},
        timeout=10,
    )
    print(f"Status: {response.status_code}")
    print(response.text[:200])
except Exception as e:
    print(f"Exception: {e}")
