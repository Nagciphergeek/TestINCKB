# Incident2KB AI

A scalable, maintainable solution to convert incident resolution notes into publish-ready knowledge base articles using AI and review workflows.

## Overview
Incident2KB is designed for maintenance and operations teams who resolve recurring incidents but lack up-to-date knowledge base articles. It provides:

- AI-powered KB article generation
- PII-aware incident anonymization
- Article review, approval, and six-month review scheduling
- Integration connectors for Jira, ServiceNow, and Confluence
- A backend API layer via FastAPI
- A Streamlit front-end for demo and user workflows
- Local or cloud-ready storage via SQLAlchemy

## Architecture

- `app.py` — Streamlit launcher for the UI
- `ui/streamlit_app.py` — Modular front-end pages
- `services/` — Business logic and integrations
- `backend/main.py` — FastAPI API endpoints
- `notebooks/` — Pipeline and model documentation

## Quick Start

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and update values.

```bash
copy .env.example .env
```

3. Run the Streamlit app locally

```bash
streamlit run app.py
```

4. Optionally run the backend API

```bash
uvicorn backend.main:app --reload
```

5. Run tests

```bash
python run_tests.py
```

### Optional PostgreSQL local setup

To run with Postgres instead of SQLite, set `DATABASE_URL` in your `.env`:

```text
DATABASE_URL=postgresql://incident2kb:incident2kb@localhost:5432/incident2kb
```

Make sure the database exists and is reachable.

### Free local evaluation option

The repository works fully in free mode using SQLite and local open-source model support for semantic similarity.
- `DATABASE_URL=sqlite:///kb_articles.db` (default)
- `sentence-transformers` + `faiss-cpu` for local embeddings
- `HUGGINGFACE_API_TOKEN` can be used with Hugging Face free model APIs
- No paid connector service is required to evaluate the app

### Run with Docker

Build and start containers locally:

```bash
docker build -t incident2kb .
docker compose up --build
```

This launchs:
- Streamlit UI on `http://localhost:8501`
- FastAPI backend on `http://localhost:8000`
- PostgreSQL on `localhost:5432`

If you only want the app without PostgreSQL, you can use the default local SQLite configuration.

## Features

- Structured KB generation with category, severity, symptoms, root cause, resolution, validation, preventive measures, and connectors.
- Review workflow with knowledge manager approval and review schedule enforcement.
- Six-month review due date auto-calculation and overdue tracking.
- Connector helpers for Jira, ServiceNow, and Confluence.
- Local SQLite demo storage with SQLAlchemy and future migration support for PostgreSQL.
- Semantic duplicate detection with sentence-transformers and FAISS.
- PDF export and Markdown download.

## Development Notes

- Use `DATABASE_URL` to swap to PostgreSQL or another SQLAlchemy-compatible database.
- `LLM_PROVIDER=litellm` is the default, but the client also supports `openai`, `azure`, and `huggingface`.
- The system is built for demo use and extensibility in production tooling.

## Connector notes and free options

- Jira Cloud: Atlassian offers a free tier for up to 10 users, which is enough for evaluation and small teams.
- Confluence Cloud: Atlassian offers a free plan for small teams and evaluation.
- ServiceNow: free developer instances are available at developer.servicenow.com for sandbox and integration testing.
- Local evaluation: you can use the app without connector credentials and still generate, save, review, and export KB articles.

### Free connector guidance

1. Create a Jira Cloud site on Atlassian's free tier.
2. Create a Confluence Cloud space on Atlassian's free tier.
3. Register for a ServiceNow developer instance for sandbox testing.
4. Use the connector credentials in `.env` only after validating the app locally.

If you need only free connectivity for an evaluation, start with Jira Cloud and Confluence Cloud, then switch ServiceNow to a developer instance for proofs of concept.

## Deployment examples

### Railway / Render / Vercel

This repository includes a `Dockerfile` and `docker-compose.yml` so you can deploy using any container-based platform.

For Railway and Render, use the Docker deployment path and set environment variables from your platform dashboard.

For Vercel, use the Docker deployment option and expose the app port with:

```text
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Recommended deployment flow

1. Deploy the `Dockerfile` to the platform.
2. Add required environment variables:
   - `LLM_PROVIDER`
   - `LLM_API_KEY`
   - `LLM_MODEL`
   - `LITELLM_API_URL`
   - `DATABASE_URL`
   - connector credentials if used
3. For production, use PostgreSQL with `DATABASE_URL=postgresql://...` and secure credentials.
4. If you want a separate backend API, point the UI to the backend service or use the same image with `uvicorn`.

## Example workflow

1. Paste incident notes.
2. Generate a KB article with AI.
3. Save and publish connector references.
4. Review and approve content.
5. Track review status and due dates from the dashboard.

## Notebook and pipeline

See `notebooks/pipeline_overview.ipynb` for an annotated pipeline overview and example prompt workflow.
