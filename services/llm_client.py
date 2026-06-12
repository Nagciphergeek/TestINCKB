"""
services/llm_client.py
Multi-provider LLM client with support for LiteLLM, OpenAI, Azure OpenAI, and HuggingFace.
"""
import os
import json
import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "litellm").lower()
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "azure/genailab-maas-gpt-4.1")
LITELLM_URL = os.getenv("LITELLM_API_URL", "https://genailab.tcs.in/v1/chat/completions")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "")
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "gpt2")

KB_SYSTEM_PROMPT = """You are a senior IT Knowledge Management expert and technical writer.

Convert raw incident resolution notes into a standardized, professional Knowledge Base article in Markdown.

Output EXACTLY this structure:

# <Concise Descriptive Title>

**Category:** <Network / Database / Application / Auth / Storage / OS / Security>
**Severity:** <Low | Medium | High | Critical>
**Tags:** <comma-separated keywords>

## Summary
2-3 sentence description of the problem and resolution.

## Symptoms
- Bullet list of all observable symptoms reported

## Root Cause
Clear technical explanation of the underlying cause.

## Resolution Steps
1. Numbered, reproducible steps.
2. Include exact commands in code blocks where relevant.
```bash
# example command
```

## Validation Steps
How to confirm the fix is working correctly.

## Preventive Measures
- Bullet list of actions to prevent recurrence.

## Affected Systems
- List of systems, services, or components involved.

## References
- Related runbooks, documentation, or tickets (or "N/A").

## Review Checklist
- Review status: Pending
- Review due date: 6 months after approval
- Reviewer: Knowledge Manager

## Connector References
- Jira ticket: Not specified.
- ServiceNow record: Not specified.
- Confluence page: Not specified.

Rules:
- Be concise, professional, and vendor-neutral.
- Do NOT invent facts not present in the input.
- If information is missing, write "Not specified."
- Anonymize any emails, IPs, usernames, or ticket numbers already replaced with placeholders.
"""


def _parse_response(response_json):
    if isinstance(response_json, dict):
        if "choices" in response_json and response_json["choices"]:
            choice = response_json["choices"][0]
            message = choice.get("message", {})
            if message.get("content"):
                return message["content"].strip()
            if choice.get("text"):
                return choice["text"].strip()
        for key in ["text", "output", "result", "completion", "response"]:
            if key in response_json and response_json[key]:
                return str(response_json[key]).strip()
    if isinstance(response_json, list) and response_json:
        item = response_json[0]
        if isinstance(item, dict) and item.get("generated_text"):
            return item["generated_text"].strip()
    return None


def call_llm(prompt: str, system: str = KB_SYSTEM_PROMPT, temperature: float = 0.3, max_tokens: int = 1600) -> str:
    if not LLM_API_KEY:
        return "[ERROR] LLM_API_KEY is not set in your .env file."

    provider = LLM_PROVIDER
    if provider == "litellm":
        endpoint = LITELLM_URL
    elif provider == "openai":
        endpoint = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
    elif provider == "azure":
        if not AZURE_ENDPOINT or not AZURE_DEPLOYMENT:
            return "[ERROR] AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_DEPLOYMENT not configured."
        endpoint = f"{AZURE_ENDPOINT}/openai/deployments/{AZURE_DEPLOYMENT}/chat/completions?api-version=2023-05-15"
    elif provider == "huggingface":
        if not HUGGINGFACE_API_TOKEN:
            return "[ERROR] HUGGINGFACE_API_TOKEN is not set."
        endpoint = os.getenv("HUGGINGFACE_API_URL", f"https://api-inference.huggingface.co/models/{HUGGINGFACE_MODEL}")
    else:
        return f"[ERROR] Unsupported LLM_PROVIDER: {provider}"

    headers = {"Content-Type": "application/json"}
    if provider in {"litellm", "openai", "azure"}:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"
        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
    else:
        headers["Authorization"] = f"Bearer {HUGGINGFACE_API_TOKEN}"
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "return_full_text": False,
            },
        }

    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=120, verify=False)
        if response.ok:
            parsed = _parse_response(response.json())
            if parsed:
                return parsed
            return "[LLM Error] Unexpected response format."
        return f"[LLM HTTP {response.status_code}] {response.text[:300]}"
    except requests.exceptions.Timeout:
        return "[LLM Error] Request timed out (120s)."
    except requests.exceptions.RequestException as exc:
        return f"[LLM Request Error] {str(exc)[:300]}"
    except json.JSONDecodeError as exc:
        return f"[LLM Parse Error] Invalid JSON response: {str(exc)[:200]}"
    except Exception as exc:
        return f"[LLM Unexpected Error] {str(exc)[:200]}"
