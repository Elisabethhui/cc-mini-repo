import requests
import json

# 配置信息
api_key = "ef2b1bfe2df4180b6886d93062cce392:OGRhODk4NjBiODYwMzI5NWUyYmJlYWNl"  # 请替换为完整密钥
base_url = "https://maas-coding-api.cn-huabei-1.xf-yun.com/v2"
import requests

# 你的配置
API_KEY = "ef2b1bfe2df4180b6886d93062cce392:OGRhODk4NjBiODYwMzI5NWUyYmJlYWNl"  # 替换成完整 Key
BASE_URL = "https://maas-coding-api.cn-huabei-1.xf-yun.com"

URL = "https://maas-coding-api.cn-huabei-1.xf-yun.com/anthropic"

headers = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY,          # 关键：通过这个头传递密钥
    "anthropic-version": "2023-06-01"
}

payload = {
    "model": "astron-code-latest",
    "messages": [{"role": "user", "content": "Say hello"}],
    "max_tokens": 50
}

response = requests.post(URL, headers=headers, json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")