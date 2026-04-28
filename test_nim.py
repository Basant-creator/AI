import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('NVIDIA_API_KEY')

print("Testing NIM connectivity with moonshotai/kimi-k2-instruct")

try:
    response = requests.post(
        'https://integrate.api.nvidia.com/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        json={'model': 'moonshotai/kimi-k2-instruct', 'messages': [{'role': 'user', 'content': 'hi'}], 'max_tokens': 10},
        timeout=30,
    )
    print(f"Status: {response.status_code}")
    print(response.text[:200])
except Exception as e:
    print(f"Exception: {e}")
