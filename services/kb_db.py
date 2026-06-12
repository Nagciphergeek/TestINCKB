"""
services/kb_db.py
Database CRUD operations for Knowledge Base articles and incident logging.
"""
from contextlib import contextmanager
from datetime import datetime, timedelta
from sqlalchemy import or_, func
from .db import create_engine_for_url, get_database_url, get_session
from .models import KBArticle, Incident, ArticleFeedback
from .review import calculate_review_due_date


@contextmanager
def database_session(db_path: str | None = None):
    session = get_session(db_path)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        try:
            session.get_bind().dispose()
        except Exception:
            pass


def _row_to_dict(row):
    data = {col.name: getattr(row, col.name) for col in row.__table__.columns}
    for key in ["created_at", "updated_at", "last_reviewed_at", "review_due_date"]:
        value = data.get(key)
        if value is not None:
            data[key] = value.isoformat()
    return data


def init_db(db_path: str | None = None):
    url = get_database_url(db_path)
    engine = create_engine_for_url(url)
    from .db import Base

    Base.metadata.create_all(engine)
    engine.dispose()


def insert_article(
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
    review_due_date: str | None = None,
    db_path: str | None = None,
) -> int:
    now = datetime.utcnow()
    due_date = calculate_review_due_date(now) if review_due_date is None else review_due_date
    with database_session(db_path) as session:
        article_row = KBArticle(
            title=title,
            article=article,
            category=category,
            severity=severity,
            tags=tags,
            review_status=review_status,
            approval_status=approval_status,
            reviewer=reviewer,
            approval_notes=approval_notes,
            jira_ticket=jira_ticket,
            servicenow_record=servicenow_record,
            confluence_page_url=confluence_page_url,
            review_due_date=due_date,
        )
        session.add(article_row)
        session.flush()
        return article_row.id


def insert_incident(raw_text: str, anonymized_text: str, kb_article_id: int, db_path: str | None = None) -> int:
    with database_session(db_path) as session:
        incident = Incident(
            raw_text=raw_text,
            anonymized_text=anonymized_text,
            kb_article_id=kb_article_id,
        )
        session.add(incident)
        session.flush()
        return incident.id


def get_all_articles(include_archived: bool = False, db_path: str | None = None) -> list:
    with database_session(db_path) as session:
        query = session.query(KBArticle)
        if not include_archived:
            query = query.filter(KBArticle.is_archived.is_(False))
        rows = query.order_by(KBArticle.created_at.desc()).all()
        return [_row_to_dict(row) for row in rows]


def get_article_by_id(article_id: int, db_path: str | None = None) -> dict | None:
    with database_session(db_path) as session:
        row = session.query(KBArticle).filter(KBArticle.id == article_id).first()
        return _row_to_dict(row) if row else None


def search_articles(keyword: str, db_path: str | None = None) -> list:
    q = f"%{keyword}%"
    with database_session(db_path) as session:
        rows = (
            session.query(KBArticle)
            .filter(
                or_(
                    KBArticle.title.ilike(q),
                    KBArticle.tags.ilike(q),
                    KBArticle.article.ilike(q),
                )
            )
            .order_by(KBArticle.created_at.desc())
            .all()
        )
        return [_row_to_dict(row) for row in rows]


def update_review_status(
    article_id: int,
    status: str,
    reviewer: str | None = None,
    approval_notes: str | None = None,
    usefulness_score: int | None = None,
    usefulness_reason: str | None = None,
    db_path: str | None = None,
):
    with database_session(db_path) as session:
        article = session.query(KBArticle).filter(KBArticle.id == article_id).first()
        if not article:
            return
        article.review_status = status
        if status == "Approved":
            article.approval_status = "Approved"
        elif status == "Needs Review":
            article.approval_status = "Pending"
        article.reviewer = reviewer or article.reviewer
        article.approval_notes = approval_notes or article.approval_notes
        if usefulness_score is not None:
            article.usefulness_score = usefulness_score
        if usefulness_reason is not None:
            article.usefulness_reason = usefulness_reason
        if status in {"Approved", "Needs Review"}:
            article.last_reviewed_at = datetime.utcnow()
            article.review_due_date = calculate_review_due_date(article.last_reviewed_at)


def archive_article(article_id: int, db_path: str | None = None):
    with database_session(db_path) as session:
        article = session.query(KBArticle).filter(KBArticle.id == article_id).first()
        if article:
            article.is_archived = True


def delete_article(article_id: int, db_path: str | None = None):
    with database_session(db_path) as session:
        article = session.query(KBArticle).filter(KBArticle.id == article_id).first()
        if article:
            session.delete(article)


def save_feedback(article_id: int, useful: bool, reason: str = "", db_path: str | None = None) -> int:
    with database_session(db_path) as session:
        feedback = ArticleFeedback(
            kb_article_id=article_id,
            useful=useful,
            reason=reason,
        )
        session.add(feedback)
        session.flush()
        article = session.query(KBArticle).filter(KBArticle.id == article_id).first()
        if article:
            article.usefulness_score = 1 if useful else 0
            article.usefulness_reason = reason
        return feedback.id


def get_stats(db_path: str | None = None) -> dict:
    with database_session(db_path) as session:
        total = session.query(func.count(KBArticle.id)).scalar() or 0
        by_status = {status: count for status, count in session.query(KBArticle.review_status, func.count(KBArticle.id)).group_by(KBArticle.review_status).all()}
        by_severity = {severity: count for severity, count in session.query(KBArticle.severity, func.count(KBArticle.id)).filter(KBArticle.severity != "").group_by(KBArticle.severity).all()}
        by_category = {category: count for category, count in session.query(KBArticle.category, func.count(KBArticle.id)).filter(KBArticle.category != "").group_by(KBArticle.category).all()}
        return {
            "total": total,
            "by_status": by_status,
            "by_severity": by_severity,
            "by_category": by_category,
        }


def get_overdue_reviews(days_overdue: int = 0, db_path: str | None = None) -> list:
    threshold = datetime.utcnow()
    with database_session(db_path) as session:
        rows = (
            session.query(KBArticle)
            .filter(KBArticle.review_due_date != None)
            .filter(KBArticle.review_due_date < threshold)
            .filter(KBArticle.is_archived.is_(False))
            .order_by(KBArticle.review_due_date.asc())
            .all()
        )
        return [_row_to_dict(row) for row in rows]


def get_due_soon_reviews(days: int = 30, db_path: str | None = None) -> list:
    now = datetime.utcnow()
    future = now + timedelta(days=days)
    with database_session(db_path) as session:
        rows = (
            session.query(KBArticle)
            .filter(KBArticle.review_due_date != None)
            .filter(KBArticle.review_due_date >= now)
            .filter(KBArticle.review_due_date <= future)
            .filter(KBArticle.is_archived.is_(False))
            .order_by(KBArticle.review_due_date.asc())
            .all()
        )
        return [_row_to_dict(row) for row in rows]
