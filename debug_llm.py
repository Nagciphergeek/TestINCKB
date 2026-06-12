#!/usr/bin/env python
"""
debug_llm.py
Quick test to verify the LLM API connection.
Run: python debug_llm.py
"""
import os
import json
import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

endpoint = os.getenv("LITELLM_API_URL", "https://api.openai.com/v1/chat/completions")
api_key  = os.getenv("LLM_API_KEY", "")
model    = os.getenv("LLM_MODEL", "gpt-4")
skip_ssl = os.getenv("LLM_SKIP_SSL_VERIFY", "true").lower() == "true"

print("=" * 60)
print("Incident2KB — LLM API Connection Test")
print("=" * 60)
print(f"Endpoint : {endpoint}")
print(f"Model    : {model}")
print(f"API Key  : {api_key[:12]}..." if api_key else "API Key  : NOT SET")
print(f"SSL Verify: {not skip_ssl}")
print()

if not api_key:
    print("ERROR: LLM_API_KEY is not set in .env")
    exit(1)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}
payload = {
    "model": model,
    "messages": [{"role": "user", "content": "Reply with exactly: CONNECTION_OK"}],
    "temperature": 0.0,
    "max_tokens": 20,
}

print("Sending test request...")
try:
    r = requests.post(endpoint, json=payload, headers=headers, timeout=30, verify=not skip_ssl)
    print(f"HTTP Status : {r.status_code}")
    if r.ok:
        j = r.json()
        content = j.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"Response    : {content}")
        print("\n✅ LLM connection SUCCESSFUL")
    else:
        print(f"Response    : {r.text[:300]}")
        print("\n❌ LLM connection FAILED — check API key and endpoint")
except Exception as e:
    print(f"Exception   : {e}")
    print("\n❌ LLM connection FAILED — check LITELLM_API_URL")
