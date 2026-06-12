"""
backend/main.py
FastAPI backend exposing KB article CRUD, review workflow, and integration endpoints.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

from services.kb_db import (
    init_db,
    insert_article,
    get_all_articles,
    get_article_by_id,
    search_articles,
    update_review_status,
    insert_incident,
    save_feedback,
    get_overdue_reviews,
    get_due_soon_reviews,
    archive_article,
    delete_article,
)
from services.integrations import create_jira_issue, create_servicenow_record, publish_confluence_page

app = FastAPI(title="Incident2KB API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


class ArticlePayload(BaseModel):
    title: str
    article: str
    category: Optional[str] = ""
    severity: Optional[str] = ""
    tags: Optional[str] = ""
    review_status: Optional[str] = "New"
    approval_status: Optional[str] = "Pending"
    reviewer: Optional[str] = ""
    approval_notes: Optional[str] = ""
    jira_ticket: Optional[str] = ""
    servicenow_record: Optional[str] = ""
    confluence_page_url: Optional[str] = ""
    raw_incident: Optional[str] = ""
    anonymized_incident: Optional[str] = ""


class ReviewPayload(BaseModel):
    review_status: str
    reviewer: Optional[str] = None
    approval_notes: Optional[str] = None
    usefulness_score: Optional[int] = None
    usefulness_reason: Optional[str] = None


class FeedbackPayload(BaseModel):
    useful: bool
    reason: Optional[str] = ""
    provided_by: Optional[str] = "SME"


class JiraPayload(BaseModel):
    summary: str
    description: str
    project_key: Optional[str] = "KB"
    issuetype: Optional[str] = "Task"


class ServiceNowPayload(BaseModel):
    short_description: str
    description: str
    record_type: Optional[str] = "incident"


class ConfluencePayload(BaseModel):
    space_key: str
    title: str
    content: str
    parent_id: Optional[str] = None


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/articles", response_model=List[dict])
def api_get_all_articles():
    return get_all_articles()


@app.get("/articles/{article_id}")
def api_get_article(article_id: int):
    article = get_article_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@app.get("/articles/search", response_model=List[dict])
def api_search_articles(q: str):
    return search_articles(q)


@app.post("/articles", response_model=dict)
def api_create_article(payload: ArticlePayload):
    article_id = insert_article(
        title=payload.title,
        article=payload.article,
        category=payload.category,
        severity=payload.severity,
        tags=payload.tags,
        review_status=payload.review_status,
        approval_status=payload.approval_status,
        reviewer=payload.reviewer,
        approval_notes=payload.approval_notes,
        jira_ticket=payload.jira_ticket,
        servicenow_record=payload.servicenow_record,
        confluence_page_url=payload.confluence_page_url,
    )
    if payload.raw_incident or payload.anonymized_incident:
        insert_incident(payload.raw_incident or "", payload.anonymized_incident or "", article_id)
    return {"id": article_id}


@app.put("/articles/{article_id}/review", response_model=dict)
def api_update_review(article_id: int, payload: ReviewPayload):
    update_review_status(
        article_id,
        payload.review_status,
        reviewer=payload.reviewer,
        approval_notes=payload.approval_notes,
        usefulness_score=payload.usefulness_score,
        usefulness_reason=payload.usefulness_reason,
    )
    return {"status": "updated"}


@app.post("/articles/{article_id}/feedback", response_model=dict)
def api_article_feedback(article_id: int, payload: FeedbackPayload):
    save_feedback(article_id, payload.useful, payload.reason)
    return {"status": "feedback_saved"}


@app.get("/reviews/overdue", response_model=List[dict])
def api_overdue_reviews():
    return get_overdue_reviews()


@app.get("/reviews/due-soon", response_model=List[dict])
def api_due_soon_reviews():
    return get_due_soon_reviews()


@app.post("/integrations/jira")
def api_create_jira(payload: JiraPayload):
    return create_jira_issue(payload.summary, payload.description, payload.project_key, payload.issuetype)


@app.post("/integrations/servicenow")
def api_create_servicenow(payload: ServiceNowPayload):
    return create_servicenow_record(payload.short_description, payload.description, payload.record_type)


@app.post("/integrations/confluence")
def api_create_confluence(payload: ConfluencePayload):
    return publish_confluence_page(payload.space_key, payload.title, payload.content, payload.parent_id)


@app.delete("/articles/{article_id}")
def api_delete_article(article_id: int):
    delete_article(article_id)
    return {"status": "deleted"}


@app.put("/articles/{article_id}/archive")
def api_archive_article(article_id: int):
    archive_article(article_id)
    return {"status": "archived"}
