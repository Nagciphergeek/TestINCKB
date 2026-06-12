"""
ui/api_client.py
HTTP client for Streamlit to communicate with FastAPI backend.
All service calls go through the API instead of direct imports.
"""
import os
import requests
from typing import List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")


class APIClient:
    """HTTP client for FastAPI backend endpoints."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.timeout = 30

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make HTTP request to backend."""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                resp = requests.get(url, timeout=self.timeout, **kwargs)
            elif method == "POST":
                resp = requests.post(url, timeout=self.timeout, **kwargs)
            elif method == "PUT":
                resp = requests.put(url, timeout=self.timeout, **kwargs)
            elif method == "DELETE":
                resp = requests.delete(url, timeout=self.timeout, **kwargs)
            else:
                return {"error": f"Unsupported method: {method}"}
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def health_check(self) -> bool:
        """Check if backend is available."""
        result = self._request("GET", "/health")
        return result.get("status") == "ok"

    def get_all_articles(self) -> List[dict]:
        """Fetch all articles."""
        result = self._request("GET", "/articles")
        return result if isinstance(result, list) else []

    def get_article(self, article_id: int) -> Optional[dict]:
        """Fetch single article."""
        result = self._request("GET", f"/articles/{article_id}")
        return result if "error" not in result else None

    def search_articles(self, query: str) -> List[dict]:
        """Search articles."""
        result = self._request("GET", "/articles/search", params={"q": query})
        return result if isinstance(result, list) else []

    def create_article(
        self,
        title: str,
        article: str,
        category: str = "",
        severity: str = "",
        tags: str = "",
        review_status: str = "New",
        approval_status: str = "Pending",
        reviewer: str = "",
        approval_notes: str = "",
        jira_ticket: str = "",
        servicenow_record: str = "",
        confluence_page_url: str = "",
        raw_incident: str = "",
        anonymized_incident: str = "",
    ) -> Optional[int]:
        """Create new article."""
        payload = {
            "title": title,
            "article": article,
            "category": category,
            "severity": severity,
            "tags": tags,
            "review_status": review_status,
            "approval_status": approval_status,
            "reviewer": reviewer,
            "approval_notes": approval_notes,
            "jira_ticket": jira_ticket,
            "servicenow_record": servicenow_record,
            "confluence_page_url": confluence_page_url,
            "raw_incident": raw_incident,
            "anonymized_incident": anonymized_incident,
        }
        result = self._request("POST", "/articles", json=payload)
        return result.get("id") if "id" in result else None

    def update_review_status(
        self,
        article_id: int,
        review_status: str,
        reviewer: Optional[str] = None,
        approval_notes: Optional[str] = None,
        usefulness_score: Optional[int] = None,
        usefulness_reason: Optional[str] = None,
    ) -> bool:
        """Update review status."""
        payload = {
            "review_status": review_status,
            "reviewer": reviewer,
            "approval_notes": approval_notes,
            "usefulness_score": usefulness_score,
            "usefulness_reason": usefulness_reason,
        }
        result = self._request("PUT", f"/articles/{article_id}/review", json=payload)
        return "error" not in result

    def save_feedback(self, article_id: int, useful: bool, reason: str = "") -> bool:
        """Save feedback."""
        payload = {"useful": useful, "reason": reason}
        result = self._request("POST", f"/articles/{article_id}/feedback", json=payload)
        return "error" not in result

    def get_overdue_reviews(self) -> List[dict]:
        """Get overdue reviews."""
        result = self._request("GET", "/reviews/overdue")
        return result if isinstance(result, list) else []

    def get_due_soon_reviews(self) -> List[dict]:
        """Get reviews due soon."""
        result = self._request("GET", "/reviews/due-soon")
        return result if isinstance(result, list) else []

    def create_jira_issue(self, summary: str, description: str, project_key: str = "KB", issuetype: str = "Task") -> dict:
        """Create Jira issue."""
        payload = {"summary": summary, "description": description, "project_key": project_key, "issuetype": issuetype}
        return self._request("POST", "/integrations/jira", json=payload)

    def create_servicenow_record(self, short_description: str, description: str, record_type: str = "incident") -> dict:
        """Create ServiceNow record."""
        payload = {"short_description": short_description, "description": description, "record_type": record_type}
        return self._request("POST", "/integrations/servicenow", json=payload)

    def publish_confluence_page(self, space_key: str, title: str, content: str, parent_id: Optional[str] = None) -> dict:
        """Publish Confluence page."""
        payload = {"space_key": space_key, "title": title, "content": content, "parent_id": parent_id}
        return self._request("POST", "/integrations/confluence", json=payload)

    def delete_article(self, article_id: int) -> bool:
        """Delete article."""
        result = self._request("DELETE", f"/articles/{article_id}")
        return "error" not in result

    def archive_article(self, article_id: int) -> bool:
        """Archive article."""
        result = self._request("PUT", f"/articles/{article_id}/archive")
        return "error" not in result


# Global API client instance
client = APIClient()
