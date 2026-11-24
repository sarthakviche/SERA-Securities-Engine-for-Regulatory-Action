# SERA — Implementation Plan (local, Postgres, no deploy)

## Constraints (from the owner)
- Local only: **PostgreSQL**, no Supabase, no deployment.
- One launcher in the project folder that starts DB + backend + frontend.
- Make every decision autonomously, and aim for a hackathon-grade product.

## Phase A — Get it working end-to-end
| # | Work | Files |
|---|---|---|
| A1 | Project-local Postgres cluster (`.localdb/`, port 55432) + `DATABASE_URL` in `.env` | `.env`, launcher |
| A2 | Fix deps (`requirements.txt`), make `alembic.ini` importable (`prepend_sys_path`) | backend |
| A3 | Migration 004: extend `regulatory_documents`, `obligations`, `tasks`; add `audit_events` (hash-chained) and `org_profile` | `alembic/versions/004_*.py`, `app/models/*` |
| A4 | **SERA Engine** (`app/engine/`): one orchestrator that replaces the split Groq/LangGraph runners for the live product | new |
| | • `text.py`: PDF → numbered paragraphs with page + paragraph citations | |
| | • `llm.py`: provider chain **Anthropic → Groq → offline** with schema-validated JSON | |
| | • `offline.py`: deterministic, explainable analyser (modal-verb obligation detection, deadline/frequency parsing, entity applicability against the org profile, vague-term ambiguity flags, keyword impact mapping to departments/systems, SOP amendments, task + evidence plan) | |
| | • `orchestrator.py`: state machine `created → in_analysis → pending_approval_1 → planning → pending_approval_2 → executing → monitoring (compliant)` | |
| A5 | REST API `/api/v2/*`: documents (list, upload PDF, sync SEBI, analyse), workflows (detail, gate decisions), obligations, tasks (status + evidence), audit (+ chain verification), dashboard KPIs, org profile | `app/api_v2/` |
| A6 | Frontend data layer: replace the scripted demo context with a React-Query-backed `SeraData` provider over `/api/v2`, then rewire every page | `src/lib/*`, `src/routes/*` |
| A7 | Seed: register the PDFs already in the repo so a fresh install has real circulars | `app/engine/seed.py` |
| A8 | One-click launcher `Start SERA.cmd` (+ `.ps1`) and a desktop/folder shortcut with an icon | repo root |

## Phase B — Hackathon differentiators (from market research)
1. **Clause-level citations, no hallucinated obligations.** Every obligation stores the verbatim source sentence plus a paragraph/page reference, shown in the UI. This answers the "trust" objection judges raise against GenAI compliance tools.
2. **Human-in-the-loop gates.** Gate 1 is interpretation sign-off; Gate 2 is plan sign-off. This maps directly to SEBI's "Agentic Compliance" TechSprint framing: agents act, humans approve.
3. **Tamper-evident audit trail.** A SHA-256 hash chain over every audit event, with a "Verify chain" button. It is regulator-ready evidence.
4. **Evidence vault.** Evidence is uploaded per task, SHA-256 fingerprinted, and recorded in the audit chain. Obligation compliance rolls up from tasks.
5. **Runs fully offline / on-prem.** The deterministic engine works with zero API keys. That fits data-residency needs (SEBI CSCRF) and makes the demo reliable. It upgrades automatically to Claude or Groq when a key is set.
6. **Org-profile-aware applicability.** Onboarding stores entity types (IA / RA / Stock-broker / AMC / DP …), departments and systems. Applicability and impact mapping use it.
7. **Live compliance-health dashboard.** KPIs computed from real data: open obligations, overdue tasks, approvals pending, compliance score.
8. **Bring-your-own circular.** Upload any regulator PDF (RBI / IRDAI too), not only scraped SEBI ones.

## Phase C — Verification
- Backend: pytest for the engine + an API smoke script (upload → analyse → gate 1 → gate 2 → complete tasks → compliant → audit chain verifies).
- Frontend: walk every page in the browser against the live backend.

## Out of scope (deliberately)
Deployment, Supabase, multi-tenant auth/RBAC, Celery/Redis, vector search. These stay as documented next steps.
