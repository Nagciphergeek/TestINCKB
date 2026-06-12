"""
services/integrations.py
External system connector helpers for Jira, ServiceNow, and Confluence.
"""
import os
import json
from base64 import b64encode
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
JIRA_USER = os.getenv("JIRA_USER", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")

SNOW_INSTANCE_URL = os.getenv("SERVICENOW_INSTANCE_URL", "").rstrip("/")
SNOW_USER = os.getenv("SERVICENOW_USER", "")
SNOW_API_TOKEN = os.getenv("SERVICENOW_API_TOKEN", "")

CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "").rstrip("/")
CONFLUENCE_USER = os.getenv("CONFLUENCE_USER", "")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN", "")


def _basic_auth_header(user: str, token: str) -> dict:
    if not user or not token:
        return {}
    auth = b64encode(f"{user}:{token}".encode("utf-8")).decode("utf-8")
    return {"Authorization": f"Basic {auth}"}


def create_jira_issue(summary: str, description: str, project_key: str = "KB", issuetype: str = "Task") -> dict:
    """Create a Jira issue and return the issue key and URL."""
    if not JIRA_BASE_URL or not JIRA_USER or not JIRA_API_TOKEN:
        return {"error": "Jira is not configured."}

    url = f"{JIRA_BASE_URL}/rest/api/2/issue"
    headers = {"Content-Type": "application/json"}
    headers.update(_basic_auth_header(JIRA_USER, JIRA_API_TOKEN))
    payload = {"fields": {"project": {"key": project_key}, "summary": summary, "description": description, "issuetype": {"name": issuetype}}}

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.ok:
        data = response.json()
        return {"key": data.get("key"), "url": f"{JIRA_BASE_URL}/browse/{data.get('key')}"}
    return {"error": response.text}


def create_servicenow_record(short_description: str, description: str, record_type: str = "incident") -> dict:
    """Create a ServiceNow incident/change record and return the sys_id or URL."""
    if not SNOW_INSTANCE_URL or not SNOW_USER or not SNOW_API_TOKEN:
        return {"error": "ServiceNow is not configured."}

    url = f"{SNOW_INSTANCE_URL}/api/now/table/{record_type}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    headers.update(_basic_auth_header(SNOW_USER, SNOW_API_TOKEN))
    payload = {"short_description": short_description, "description": description}

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.ok:
        data = response.json().get("result", {})
        sys_id = data.get("sys_id")
        return {"sys_id": sys_id, "url": f"{SNOW_INSTANCE_URL}/nav_to.do?uri=/{record_type}.do?sys_id={sys_id}"}
    return {"error": response.text}


def publish_confluence_page(space_key: str, title: str, content: str, parent_id: Optional[str] = None) -> dict:
    """Publish a page to Confluence and return the page link or error."""
    if not CONFLUENCE_URL or not CONFLUENCE_USER or not CONFLUENCE_API_TOKEN:
        return {"error": "Confluence is not configured."}

    url = f"{CONFLUENCE_URL}/wiki/rest/api/content"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    headers.update(_basic_auth_header(CONFLUENCE_USER, CONFLUENCE_API_TOKEN))
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": {"storage": {"value": content, "representation": "storage"}},
    }
    if parent_id:
        payload["ancestors"] = [{"id": parent_id}]

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.ok:
        data = response.json()
        return {"id": data.get("id"), "url": f"{CONFLUENCE_URL}/wiki{data.get('links', {}).get('webui', '')}"}
    return {"error": response.text}
