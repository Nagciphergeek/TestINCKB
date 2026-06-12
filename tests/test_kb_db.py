"""tests/test_kb_db.py — Unit tests for KB database operations."""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.kb_db import (
    init_db, insert_article, get_all_articles, get_article_by_id,
    search_articles, update_review_status, delete_article, get_stats
)

SAMPLE_ARTICLE = """# Database Connection Pool Exhausted

**Category:** Database
**Severity:** High
**Tags:** database, connection-pool, performance

## Summary
Connection pool exhausted during peak load.

## Root Cause
Long-running queries held connections.

## Resolution Steps
1. Killed the blocking query.
2. Increased pool size to 100.
"""


def _tmp_db():
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    f.close()
    init_db(f.name)
    return f.name


def test_insert_and_retrieve():
    db = _tmp_db()
    art_id = insert_article("Test Title", SAMPLE_ARTICLE, category="Database",
                            severity="High", tags="db,test", db_path=db)
    assert art_id > 0
    art = get_article_by_id(art_id, db_path=db)
    assert art is not None
    assert art["title"] == "Test Title"
    assert art["category"] == "Database"
    os.unlink(db)


def test_get_all_articles():
    db = _tmp_db()
    insert_article("Article 1", "body 1", db_path=db)
    insert_article("Article 2", "body 2", db_path=db)
    all_arts = get_all_articles(db_path=db)
    assert len(all_arts) == 2
    os.unlink(db)


def test_search_articles():
    db = _tmp_db()
    insert_article("Login Failure SSO", "SAML cert expired", tags="auth,sso", db_path=db)
    insert_article("Disk Full Alert", "Log volume at 98%", tags="storage,disk", db_path=db)
    results = search_articles("SSO", db_path=db)
    assert len(results) == 1
    assert "SSO" in results[0]["title"]
    os.unlink(db)


def test_update_review_status():
    db = _tmp_db()
    art_id = insert_article("Title", "body", db_path=db)
    update_review_status(art_id, "Approved", db_path=db)
    art = get_article_by_id(art_id, db_path=db)
    assert art["review_status"] == "Approved"
    os.unlink(db)


def test_delete_article():
    db = _tmp_db()
    art_id = insert_article("To Delete", "body", db_path=db)
    delete_article(art_id, db_path=db)
    assert get_article_by_id(art_id, db_path=db) is None
    os.unlink(db)


def test_stats():
    db = _tmp_db()
    insert_article("A1", "body", severity="High",   category="Database", review_status="Approved", db_path=db)
    insert_article("A2", "body", severity="Medium", category="Network",  review_status="New",      db_path=db)
    insert_article("A3", "body", severity="High",   category="Database", review_status="New",      db_path=db)
    stats = get_stats(db_path=db)
    assert stats["total"] == 3
    assert stats["by_severity"].get("High") == 2
    assert stats["by_category"].get("Database") == 2
    os.unlink(db)


if __name__ == "__main__":
    tests = [
        test_insert_and_retrieve,
        test_get_all_articles,
        test_search_articles,
        test_update_review_status,
        test_delete_article,
        test_stats,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ PASS  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ❌ FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
