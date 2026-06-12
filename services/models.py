"""
services/models.py
SQLAlchemy ORM models for articles, incidents, and review feedback.
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship

from .db import Base


class KBArticle(Base):
    __tablename__ = "kb_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(250), nullable=False)
    category = Column(String(80), default="")
    severity = Column(String(40), default="")
    tags = Column(String(250), default="")
    article = Column(Text, nullable=False)
    review_status = Column(String(40), default="New", index=True)
    approval_status = Column(String(40), default="Pending")
    reviewer = Column(String(120), default="")
    approval_notes = Column(Text, default="")
    last_reviewed_at = Column(DateTime, nullable=True)
    review_due_date = Column(DateTime, nullable=True)
    is_archived = Column(Boolean, default=False)
    usefulness_score = Column(Integer, nullable=True)
    usefulness_reason = Column(Text, default="")
    jira_ticket = Column(String(120), default="")
    servicenow_record = Column(String(120), default="")
    confluence_page_url = Column(String(300), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    incidents = relationship("Incident", back_populates="article", cascade="all, delete-orphan")
    feedbacks = relationship("ArticleFeedback", back_populates="article", cascade="all, delete-orphan")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(Text, nullable=False)
    anonymized_text = Column(Text, default="")
    kb_article_id = Column(Integer, ForeignKey("kb_articles.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    article = relationship("KBArticle", back_populates="incidents")


class ArticleFeedback(Base):
    __tablename__ = "article_feedback"

    id = Column(Integer, primary_key=True, index=True)
    kb_article_id = Column(Integer, ForeignKey("kb_articles.id"), nullable=False)
    useful = Column(Boolean, nullable=False)
    reason = Column(Text, default="")
    provided_by = Column(String(120), default="SME")
    created_at = Column(DateTime, default=datetime.utcnow)

    article = relationship("KBArticle", back_populates="feedbacks")
