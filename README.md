# SERA — Securities Engine for Regulatory Action

SERA turns SEBI circulars into **cited obligations → owner-assigned tasks → hash-verified evidence → regulator-ready compliance**. Agents draft; humans approve at two gates; every step lands in a tamper-evident audit trail. It runs **entirely on your machine** (PostgreSQL + FastAPI + React) with no API keys required.

## Quick start (Windows)

Double-click **`Start SERA`** (the shortcut with the SERA icon, or `Start SERA.cmd`). It will:

1. create/start a project-local PostgreSQL cluster in `.localdb/` on port **55432** (user/pw `sera`/`sera`);
2. create the Python venv + install deps (first run), apply Alembic migrations;
3. start the API on **http://127.0.0.1:8000** and the UI on **http://localhost:5173**, then open the browser.

`Stop SERA.cmd` stops everything. Requirements: PostgreSQL 15+ binaries installed (only the binaries are used, not your existing server), Python 3.12, Node 20+.

### Manual start
```powershell
cd backend; .\.venv\Scripts\python.exe -m alembic upgrade head; .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
cd frontend; npx vite dev --port 5173
```

## How it works

| Stage | What happens | Where |
|---|---|---|
| Intake | SEBI scraper/downloader, PDF upload, or PDFs in `backend/downloads/` (auto-registered on start) | `app/scraper`, `app/engine/service.py` |
| Analysis | PDF → numbered paragraphs → obligations / exemptions / timeline changes, deadlines & SLAs, applicability vs org profile, ambiguity flags, risk | `app/engine/text.py`, `analyzer.py` |
| Optional LLM | If `ANTHROPIC_API_KEY` or `GROQ_API_KEY` is set, the LLM *proposes* obligations; only those whose quote is found verbatim in the PDF are kept | `app/engine/llm.py` |
| Gate 1 | Human approves the interpretation (can exclude items) | Workspace |
| Planning | Impact map (departments/systems), SOP drafts, 3-phase task plan | Impact Map, Implementation Plan |
| Gate 2 | Human approves plan, or requests changes (feedback becomes tasks) | Implementation Plan |
| Execution | Tasks with owners/due dates, evidence upload (SHA-256), roll-up to compliance | Implementation Tracker |
| Audit | Append-only SHA-256 hash chain + verify endpoint | Audit Trail |

API: `/api/v2/*` (see `app/api_v2/router.py`, OpenAPI at http://127.0.0.1:8000/docs).

## Useful scripts (run from `backend/` with `.venv\Scripts\python.exe`)
- `scripts/reset_demo.py` – wipe workflow data for a clean demo (circulars re-seed on next start)
- `scripts/smoke_v2.py` – end-to-end API test (analyse → gates → evidence → compliant → verify chain)
- `scripts/tamper_demo.py [--undo]` – edit an audit row to demonstrate tamper detection
- `python -m pytest tests/engine` – engine unit tests

## Docs
- `docs/01_STATUS_REPORT.md` – audit of what existed and what was incomplete
- `docs/02_IMPLEMENTATION_PLAN.md` – the plan that was executed
- `docs/03_HACKATHON_STRATEGY.md` – market research, positioning, pitch
- `docs/04_DEMO_SCRIPT.md` – 4-minute live demo walkthrough

## Notes
- Email notifications (Resend) are disabled in `backend/.env` for local dev (`EMAIL_ENABLED=false`).
- Scanned (image-only) PDFs are detected and **not** analysed (fail-closed) – OCR is on the roadmap.
- The older Groq pipeline (`/api/v1/pipeline`) and LangGraph slice (`app/ai/graph`) are kept for reference; the product uses the v2 engine.
