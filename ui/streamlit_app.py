"""
ui/streamlit_app.py
Streamlit interface for Incident2KB with KB generation, review workflow, connector links, and dashboard.
Communicates with FastAPI backend via HTTP instead of direct service calls.
"""
import os
import re
from datetime import datetime

import streamlit as st
from services.anonymizer import anonymize, anonymize_report
from services.kb_generator import generate_kb_article
from services.pdf_generator import create_kb_pdf
from services.vector_search import find_similar_articles
from ui.api_client import client as api_client


def run():
    """Initialize Streamlit app and check backend connection."""
    # Check if backend is available
    if not api_client.health_check():
        st.error("⚠️ Cannot connect to FastAPI backend. Make sure it's running on " + api_client.base_url)
        return

    st.set_page_config(page_title="Incident2KB AI", page_icon="📚", layout="wide")

    st.sidebar.image("https://img.icons8.com/fluency/48/knowledge-sharing.png", width=40)
    st.sidebar.title("Incident2KB AI")
    st.sidebar.caption("Generate, review, and publish knowledge base articles from incident notes")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigate",
        ["Generate Article", "Article Library", "Dashboard"],
        index=0,
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("LLM & Review Settings")
    do_anonymize = st.sidebar.checkbox("Auto-anonymize input", value=True)
    similarity_threshold = st.sidebar.slider("Duplicate similarity threshold", 0.5, 1.0, 0.82, 0.01)
    default_status = st.sidebar.selectbox("Default approval status", ["New", "Approved", "Needs Review"], index=0)
    st.sidebar.markdown("---")
    st.sidebar.caption(f"LLM provider: `{os.getenv('LLM_PROVIDER', 'litellm')}`")
    st.sidebar.caption(f"Database URL: `{os.getenv('DATABASE_URL', 'sqlite:///kb_articles.db')}`")

    if page == "Generate Article":
        render_generate_page(do_anonymize, similarity_threshold, default_status)
    elif page == "Article Library":
        render_library_page()
    else:
        render_dashboard()


SAMPLE_INCIDENTS = {
    "Database connection pool exhausted": (
        "Users reported app freezing at 3pm. INC-4521 raised. Checked srv-db-02 — connection pool exhausted (max 50). "
        "Identified long-running report query holding connections for 8+ minutes. Killed PID 8821, increased pool to 100, added index on orders.created_at. "
        "App recovered in 5 minutes. Notified john.doe@acme.com."
    ),
    "SAML certificate expired (login failures)": (
        "Multiple users from 10.0.5.23 couldn't log in via SSO. SAML signing cert expired on auth-prod-01. "
        "Renewed cert via internal CA (valid 2 years), restarted Tomcat, validated with test account test@corp.com. "
        "Set 30-day calendar reminder. TKT-9871 resolved."
    ),
    "Disk full — log volume": (
        "Monitoring alert: /var/log on host-app-07 at 98%. App writes > 2GB/day of DEBUG logs. "
        "Rotated logs, archived 90-day old files to S3. Changed log level to WARN in /etc/app/config.yml. "
        "Updated logrotate to daily with 14-day retention. Alert cleared."
    ),
    "API Gateway 502 errors": (
        "INC-7742: 502 errors on /api/v2/orders endpoint from 14:00-14:45. Root cause: upstream service srv-orders-03 OOM-killed by kernel. "
        "Increased container memory limit from 512MB to 1GB in k8s manifest. Redeployed pod, errors cleared at 14:52. "
        "Added memory usage alert at 80% threshold."
    ),
}


def render_generate_page(do_anonymize: bool, similarity_threshold: float, default_status: str):
    st.title("✨ Generate KB Article")
    st.markdown("Paste incident resolution notes below, then generate a structured knowledge base article with review metadata and connector references.")

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.subheader("Incident Input")
        sample_key = st.selectbox("Load a sample incident", ["— type your own —"] + list(SAMPLE_INCIDENTS.keys()))
        incident_text = st.text_area(
            "Raw incident notes",
            value=SAMPLE_INCIDENTS.get(sample_key, "") if sample_key != "— type your own —" else "",
            height=280,
        )
        if do_anonymize and incident_text.strip():
            diff = anonymize_report(incident_text, anonymize(incident_text))
            if diff:
                with st.expander("🔒 Anonymization preview", expanded=False):
                    for label, items in diff.items():
                        st.write(f"**{label}:** {', '.join(set(str(item) for item in items))}")

        issue_status = st.selectbox("Approval status", ["New", "Approved", "Needs Review"], index=["New", "Approved", "Needs Review"].index(default_status))
        reviewer = st.text_input("Knowledge manager / reviewer", value="")
        approval_notes = st.text_area("Approval notes", value="", height=100)
        jira_ticket = st.text_input("Jira ticket reference", value="")
        servicenow_record = st.text_input("ServiceNow record reference", value="")
        confluence_page_url = st.text_input("Confluence page URL", value="")

        if st.button("✨ Generate KB Article", type="primary"):
            if not incident_text.strip():
                st.warning("Enter incident notes before generating an article.")
                return
            cleaned = anonymize(incident_text) if do_anonymize else incident_text
            st.session_state["incident_text"] = incident_text
            st.session_state["cleaned_text"] = cleaned
            st.session_state["generated_article"] = generate_kb_article(cleaned)
            st.session_state["reviewer"] = reviewer
            st.session_state["issue_status"] = issue_status
            st.session_state["approval_notes"] = approval_notes
            st.session_state["jira_ticket"] = jira_ticket
            st.session_state["servicenow_record"] = servicenow_record
            st.session_state["confluence_page_url"] = confluence_page_url
            st.session_state["duplicate_warning"] = False

    with right:
        st.subheader("Generated Article")

        if "generated_article" in st.session_state:
            article = st.session_state["generated_article"]
            if article.startswith("[ERROR]"):
                st.error(article)
                return

            title = extract_title(article)
            category = extract_metadata(article, "Category")
            severity = extract_metadata(article, "Severity")
            tags = extract_metadata(article, "Tags")

            existing = api_client.get_all_articles()
            similars = find_similar_articles(st.session_state["cleaned_text"], existing, threshold=similarity_threshold)
            if similars:
                st.warning(f"⚠️ Found {len(similars)} similar article(s). Please review before saving.")
                for art, score in similars:
                    st.info(f"{art['id']} — {art['title']} — similarity {score:.0%}")
                st.session_state["duplicate_warning"] = True

            tabs = st.tabs(["Preview", "Markdown", "Anonymized Input"])
            with tabs[0]:
                st.markdown(article)
            with tabs[1]:
                st.code(article, language="markdown")
            with tabs[2]:
                st.text_area("Anonymized incident text", value=st.session_state["cleaned_text"], height=240)

            save_col, export_col, integration_col = st.columns(3)
            with save_col:
                if st.button("💾 Save Article"):
                    article_id = api_client.create_article(
                        title=title,
                        article=article,
                        category=category,
                        severity=severity,
                        tags=tags,
                        review_status=st.session_state["issue_status"],
                        approval_status="Approved" if st.session_state["issue_status"] == "Approved" else "Pending",
                        reviewer=st.session_state["reviewer"],
                        approval_notes=st.session_state["approval_notes"],
                        jira_ticket=st.session_state["jira_ticket"],
                        servicenow_record=st.session_state["servicenow_record"],
                        confluence_page_url=st.session_state["confluence_page_url"],
                        raw_incident=st.session_state["incident_text"],
                        anonymized_incident=st.session_state["cleaned_text"],
                    )
                    if article_id:
                        st.success(f"Saved KB article #{article_id}")
                    else:
                        st.error("Failed to save article")
            with export_col:
                markdown_file = f"kb_{slugify(title)}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
                st.download_button("⬇️ Download Markdown", data=article, file_name=markdown_file, mime="text/markdown")
                pdf_bytes = create_kb_pdf(article, title=title, review_status=st.session_state["issue_status"])
                st.download_button("⬇️ Download PDF", data=pdf_bytes, file_name=markdown_file.replace('.md', '.pdf'), mime="application/pdf")
            with integration_col:
                st.subheader("Publish Connectors")
                if st.button("Create Jira issue"):
                    result = api_client.create_jira_issue(title, article)
                    st.json(result)
                if st.button("Create ServiceNow record"):
                    result = api_client.create_servicenow_record(title, article)
                    st.json(result)
                if st.button("Publish Confluence page"):
                    result = api_client.publish_confluence_page("KB", title, article)
                    st.json(result)

        else:
            st.info("Generate an article to preview structured output here.")


def render_library_page():
    st.title("📚 KB Article Library")
    search_query = st.text_input("Search saved articles", value="")
    results = api_client.search_articles(search_query) if search_query.strip() else api_client.get_all_articles()

    st.caption(f"{len(results)} articles found")
    if not results:
        st.info("No saved articles yet. Generate one from the top menu.")
        return

    for article in results:
        status_icon = {
            "New": "🔵",
            "Approved": "🟢",
            "Needs Review": "🟠",
            "Archived": "⚫",
        }.get(article["review_status"], "⚪")

        with st.expander(f"{status_icon} #{article['id']} — {article['title']}"):
            full = api_client.get_article(article["id"])
            if not full:
                st.error("Article data unavailable")
                continue
            st.markdown(full["article"])
            meta_cols = st.columns(3)
            with meta_cols[0]:
                st.write(f"**Reviewer:** {full.get('reviewer','—')}")
                st.write(f"**Approval status:** {full.get('approval_status','—')}")
                st.write(f"**Review due:** {format_datetime(full.get('review_due_date'))}")
            with meta_cols[1]:
                st.write(f"**Jira:** {full.get('jira_ticket') or '—'}")
                st.write(f"**ServiceNow:** {full.get('servicenow_record') or '—'}")
                st.write(f"**Confluence:** {full.get('confluence_page_url') or '—'}")
            with meta_cols[2]:
                st.write(f"**Useful:** {full.get('usefulness_score') or 'Not rated'}")
                st.write(f"**Feedback:** {full.get('usefulness_reason') or '—'}")
                st.write(f"**Archived:** {full.get('is_archived')}")

            cols = st.columns([2, 1])
            with cols[0]:
                new_status = st.selectbox("Update review status", ["New", "Approved", "Needs Review", "Archived"], index=["New", "Approved", "Needs Review", "Archived"].index(full["review_status"]))
                reviewer_input = st.text_input("Reviewer", value=full.get("reviewer", ""), key=f"rev_{full['id']}")
                notes_input = st.text_area("Approval notes", value=full.get("approval_notes", ""), key=f"notes_{full['id']}", height=80)
            with cols[1]:
                useful = st.radio("Useful?", ["Yes", "No"], index=0 if full.get("usefulness_score") == 1 else 1 if full.get("usefulness_score") == 0 else 0, key=f"useful_{full['id']}")
                reason = st.text_area("Why not useful?", value=full.get("usefulness_reason", ""), key=f"reason_{full['id']}", height=80)
                if st.button("Save metadata", key=f"save_{full['id']}"):
                    api_client.update_review_status(
                        full["id"],
                        new_status,
                        reviewer=reviewer_input,
                        approval_notes=notes_input,
                        usefulness_score=1 if useful == "Yes" else 0,
                        usefulness_reason=reason,
                    )
                    api_client.save_feedback(full["id"], useful == "Yes", reason)
                    st.success("Metadata saved")
                    st.rerun()

                if st.button("Archive article", key=f"archive_{full['id']}"):
                    if api_client.archive_article(full['id']):
                        st.warning("Article archived")
                    else:
                        st.error("Failed to archive article")
                    st.rerun()

            if st.button("Delete article", key=f"delete_{full['id']}"):
                if api_client.delete_article(full['id']):
                    st.warning("Article deleted")
                else:
                    st.error("Failed to delete article")
                st.rerun()


def render_dashboard():
    st.title("📊 Knowledge Base Dashboard")
    
    # Fetch data from API
    all_articles = api_client.get_all_articles()
    overdue = api_client.get_overdue_reviews()
    due_soon = api_client.get_due_soon_reviews()

    # Calculate stats
    total = len(all_articles)
    by_status = {}
    by_severity = {}
    by_category = {}
    
    for art in all_articles:
        status = art.get("review_status", "Unknown")
        by_status[status] = by_status.get(status, 0) + 1
        severity = art.get("severity", "Unknown")
        by_severity[severity] = by_severity.get(severity, 0) + 1
        category = art.get("category", "Unknown")
        by_category[category] = by_category.get(category, 0) + 1

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total articles", total)
    c2.metric("Approved", by_status.get("Approved", 0))
    c3.metric("Needs review", by_status.get("Needs Review", 0))
    c4.metric("Overdue reviews", len(overdue))

    st.markdown("---")
    st.subheader("Review cadence")
    st.write(f"Articles overdue for review: **{len(overdue)}**")
    st.write(f"Articles due soon (30 days): **{len(due_soon)}**")
    if overdue:
        for art in overdue[:5]:
            st.write(f"• #{art['id']} — {art['title']} — due {format_datetime(art.get('review_due_date'))}")

    st.markdown("---")
    st.subheader("Breakdown by severity and category")
    import pandas as pd

    if by_severity:
        df = pd.DataFrame(list(by_severity.items()), columns=["Severity", "Count"]).set_index("Severity")
        st.bar_chart(df)
    if by_category:
        df2 = pd.DataFrame(list(by_category.items()), columns=["Category", "Count"]).set_index("Category")
        st.bar_chart(df2)

    st.markdown("---")
    st.subheader("Connector health")
    st.info("Use the Generate Article page to create Jira, ServiceNow, and Confluence records when connectors are configured.")


def extract_title(article: str) -> str:
    match = re.search(r"^#\s+(.+)$", article, re.MULTILINE)
    return match.group(1).strip() if match else "Untitled KB Article"


def extract_metadata(article: str, field: str) -> str:
    match = re.search(rf"\*\*{re.escape(field)}:\*\*\s*(.+)", article)
    return match.group(1).strip() if match else ""


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def format_datetime(value):
    if not value:
        return "Not specified"
    if isinstance(value, str):
        return value
    return value.strftime("%Y-%m-%d")


if __name__ == "__main__":
    run()
