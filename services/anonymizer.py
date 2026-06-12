"""
services/anonymizer.py
Anonymizes PII and sensitive infrastructure details from incident text
before sending to external LLM API.
"""
import re


def anonymize(text: str) -> str:
    """
    Replace sensitive tokens with safe placeholders.
    Covers: emails, IPs, hostnames, ticket IDs, usernames, passwords.
    """
    # Email addresses
    text = re.sub(r"[\w\.\+\-]+@[\w\.\-]+\.[a-zA-Z]{2,}", "[EMAIL]", text)
    # IPv4 addresses
    text = re.sub(r"\b\d{1,3}(\.\d{1,3}){3}\b", "[IP_ADDRESS]", text)
    # Ticket / incident IDs (INC-1234, TKT-5678, REQ-999, CHG-001)
    text = re.sub(r"\b(INC|TKT|REQ|CHG|PRB)[-_]?\d+\b", "[TICKET_ID]", text, flags=re.I)
    # Server / host names (srv-xxx, host-xxx, db-xxx, app-xxx)
    text = re.sub(r"\b(srv|server|host|db|app|prod|dev|uat|stg)[-_][\w\-]+\b", "[HOST]", text, flags=re.I)
    # @username mentions
    text = re.sub(r"@[A-Za-z0-9_\.]+", "[USER]", text)
    # Passwords / secrets in assignments (password=xxx, secret=xxx)
    text = re.sub(r"(password|passwd|secret|token|key)\s*[=:]\s*\S+", r"\1=[REDACTED]", text, flags=re.I)
    # Phone numbers
    text = re.sub(r"\b(\+?\d[\d\s\-\(\)]{7,14}\d)\b", "[PHONE]", text)
    return text.strip()


def anonymize_report(original: str, anonymized: str) -> dict:
    """Return a diff summary of what was anonymized."""
    patterns = {
        "Emails":    r"[\w\.\+\-]+@[\w\.\-]+\.[a-zA-Z]{2,}",
        "IPs":       r"\b\d{1,3}(\.\d{1,3}){3}\b",
        "Ticket IDs":r"\b(INC|TKT|REQ|CHG|PRB)[-_]?\d+\b",
        "Hosts":     r"\b(srv|server|host|db|app|prod|dev|uat|stg)[-_][\w\-]+\b",
    }
    found = {}
    for label, pattern in patterns.items():
        matches = re.findall(pattern, original, flags=re.I)
        if matches:
            # flatten tuples from groups
            found[label] = [m if isinstance(m, str) else m[0] for m in matches]
    return found
