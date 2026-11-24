# SERA — Repository Audit & Incomplete-Features Report

_Audit date: 2026-11-24 · Branch audited: `feat/notifications-and-implementationTracker` (commit `b18c652`)_

## 0. Which folder is the product?

`D:\development\SERA` holds several copies. The canonical one is the git repo
**`SERA-Repo/SERA-Securities-Engine-for-Regulatory-Action`**: it has the most
recent architecture (SQLAlchemy models, Alembic migrations, LangGraph agents,
notifications). `SERA-live-workflow-fixed/` and `SERA-live-workflow-updated (2)/`
are older zip snapshots of a different branch that used a Gemini service. Treat them as archives.
The other folders (`FInalVideo`, `presentationVideo`, `Demo-Videos`, `PRD`, `UI`)
hold pitch/video material.

## 1. What already exists and works

| Area | State |
|---|---|
| SEBI scraper (`app/scraper`, `workers/monitor.py`) | Works. Scrapes the circular listing, diffs it against `data/documents.json`, and downloads PDFs. Storage is JSON files, not Postgres. |
| Ingestion modules 1–7 (`app/ingestion`) | Work. PDF → spans → layout → headings → numbering → AST → clauses → semantic batches. Tests exist. No API endpoint triggers them, so they only run from scripts. |
| Groq LLM agents (`app/ai/agents/*`: extraction, applicability, ambiguity, obligation, task_generation) | Code is complete but requires `GROQ_API_KEY`, which is not set, so every pipeline run fails at stage 1. |
| LangGraph slice (`app/ai/graph`: impact mapping → SOP generation → evidence plan → Gate 2 → execution hand-off) | Code is well designed, but it only runs with Anthropic + in-memory fakes in `scripts/run_demo.py`. |
| DB schema (Alembic 001–003) | Works. `regulatory_documents`, `workflow_documents`, `obligations`, `tasks`, `notifications`, `user_notification_preferences`. |
| Notifications (in-app + SSE + Resend email + overdue checker) | Mostly works. |
| Frontend (TanStack Start + shadcn, 11 pages) | Renders well, but almost all data is **scripted demo/mock data** (`lib/demo.tsx`, `lib/mock-data.ts`). |

## 2. Incomplete / broken features (ranked by impact)

### Blockers (the product cannot run end-to-end)
1. **No LLM is configured.** There are no Groq or Anthropic keys, no local model, and no fallback, so every AI stage fails.
2. **The two AI halves are not connected.** The Groq pipeline (stages 1–5) and the Anthropic LangGraph (stages 6–8) use different providers, different stores (JSON files vs an in-memory `InMemoryOrgStore`) and different obligation shapes.
3. **The LangGraph checkpointer is wrong.**
   - `AsyncPostgresSaver.from_conn_string()` returns a context manager, not a saver.
   - It is given an `asyncpg` SQLAlchemy URL that psycopg rejects.
   - The `langgraph-checkpoint-postgres` package was not installed.
   - `resume_graph` passes `command=` to `ainvoke`, which is invalid.
   - Gate 2 resume can therefore never work.
4. **Ingestion is not reachable from the API.** The `/pipeline/process/{id}` endpoint assumes `semantic_batches.json` already exists on disk.
5. **The frontend is not wired to real data.**
   - The inbox, dashboard, obligations, register, tracker and audit pages read the demo context.
   - `api.getDocuments()` calls `/api/v1/documents`, which does not exist.
   - Only the impact-map and plan pages make partial real calls.
6. **Dependency drift.** `requirements.txt` was missing `langgraph`, `anthropic` and `psycopg`. `pyproject.toml` lists a different set. The venv was incomplete.

### Functional gaps
7. **Gate 1 (interpretation approval) has no UI or backend semantics.** The backend has a `gate/{name}` endpoint, but it does not move the status machine forward.
8. **Tasks are never materialised for the tracker.** The tracker has no status updates or evidence upload, and nothing rolls tasks up into obligation compliance.
9. **The audit trail is mock-only.** No audit table exists and nothing is tamper-evident.
10. **Onboarding (org profile) is not persisted.** Applicability is hard-coded to "Investment Adviser / Research Analyst".
11. **Users cannot upload a circular PDF.** Only scraped SEBI circulars can enter the system.
12. **The dashboard KPIs are hard-coded.**
13. **The Celery workers are empty files** (`celery_app.py`, `tasks.py`). The README claims scheduled monitoring, but none exists.
14. **The upstream LangGraph nodes are 0-byte stubs:** applicability, obligation_extraction, change_analysis, ambiguity_detection.
15. **Housekeeping:**
    - Committed `__pycache__` and `.pyc` files.
    - `documents.json` holds absolute paths from another machine (`D:\SERA\sera\...`).
    - `backend/.env` contains a real Resend key. It is git-ignored, but don't share it.
    - There is no single command to start the stack.

### Environment findings on this PC
- Postgres 18 is installed as a Windows service, but its password is unknown and port 5433 is taken. **Fix:** a project-local cluster in `.localdb/` on port **55432** (user `sera` / pw `sera`, DB `sera`). It is created and started by the launcher.
- Docker Desktop is installed but not running. Nothing depends on it.
- There is no GPU and no Ollama, so local LLM inference is not practical. **Fix:** a deterministic offline analysis engine (see the plan).
