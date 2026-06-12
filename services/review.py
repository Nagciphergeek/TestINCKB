"""
services/review.py
Utilities for review scheduling and due date calculation.
"""
from datetime import datetime, timedelta


def calculate_review_due_date(start_at: datetime | None = None, months: int = 6) -> datetime:
    """Return a review due date that is approximately N months after the given date."""
    if start_at is None:
        start_at = datetime.utcnow()
    return start_at + timedelta(days=months * 30)
