<div align="center">

<img src="assets/banner.png" alt="SERA — Securities Engine for Regulatory Action" width="100%" />

# SERA — Securities Engine for Regulatory Action

**Agentic compliance for SEBI-regulated intermediaries.** SERA turns every SEBI circular into cited obligations, owner-assigned tasks and hash-verified evidence. Agents draft, humans approve, and it runs entirely on your own machine.

[![License](https://img.shields.io/badge/License-MIT-1e293b?style=for-the-badge&logo=opensourceinitiative&logoColor=3DA639)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-1e293b?style=for-the-badge&logo=python&logoColor=3776AB)](backend/requirements.txt)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-1e293b?style=for-the-badge&logo=typescript&logoColor=3178C6)](frontend/package.json)
[![Tests](https://img.shields.io/badge/Engine_Tests-10_passing-1e293b?style=for-the-badge&logo=pytest&logoColor=0A9EDC)](backend/tests/engine/test_engine.py)
[![Domain](https://img.shields.io/badge/Domain-SEBI_RegTech-1e293b?style=for-the-badge&logo=bookstack&logoColor=F59E0B)](docs/03_HACKATHON_STRATEGY.md)

[Demo Script](docs/04_DEMO_SCRIPT.md) · [Documentation](docs/) · [Report a Bug](https://github.com/sarthakviche/SERA-Securities-Engine-for-Regulatory-Action/issues)

</div>

---

## About

SEBI issues hundreds of circulars a year. At a mid-size broker, DP, investment adviser or research analyst, a small compliance team reads each PDF, works out what applies, emails department heads and tracks everything in spreadsheets. SERA automates that loop end to end:

1. **Intake.** It scrapes circulars from sebi.gov.in, accepts uploaded PDFs, or picks up PDFs already in `backend/downloads/`.
2. **Analysis.** It splits each circular into numbered paragraphs and extracts obligations, exemptions, deadlines and event-driven SLAs. It also checks applicability against your organisation profile, flags ambiguous wording and scores risk.
3. **Gate 1.** A compliance officer approves the interpretation, and can exclude items.
4. **Planning.** SERA builds an impact map (departments and systems), drafts SOP amendments and lays out a three-phase task plan.
5. **Gate 2.** The plan is approved. If changes are requested, the reviewer's feedback becomes a tracked task.
6. **Execution.** Owners complete tasks and upload evidence, which is SHA-256 fingerprinted. Completion rolls up to obligation-level and circular-level compliance.
7. **Audit.** Every action lands in a hash-chained, tamper-evident log.

<table>
<tr>
<td width="33%" valign="top">

### 📌 Cited, verifiable analysis
Every obligation quotes its **verbatim source sentence, paragraph and page**. If an LLM is configured, it only *proposes* obligations. A proposal is discarded unless its quote is found in the PDF.

</td>
<td width="33%" valign="top">

### 🧑‍⚖️ Human-gated agents
Two approval gates: **interpretation** and **plan**. Agents draft and people decide. Unmatched departments and scanned PDFs **fail closed** and go to human review; SERA doesn't guess.

</td>
<td width="33%" valign="top">

### 🔗 Tamper-evident evidence
Each audit event is **SHA-256 chained** to the one before it. Evidence files are fingerprinted. One click verifies the whole chain, and editing any row breaks it.

</td>
</tr>
</table>

- **Offline-first.** A deterministic engine with local PostgreSQL. No API keys needed and no circular text leaves the machine.
- **Optional LLM.** Set `ANTHROPIC_API_KEY` (Claude, default `claude-opus-5-5`) or `GROQ_API_KEY`. SERA falls back to the offline engine on any failure.
- **Deadline intelligence.** Explicit dates, effective dates, extensions that update the obligation they modify, and SLAs such as "within 7 working days of closure" kept apart from one-off deadlines.
- **Org-aware applicability.** 15 SEBI intermediary types, each decision explained in plain English.
- **Regulator-ready output.** A live compliance-health dashboard and a CSV export of the compliance register.
- **One-click local launcher.** It starts Postgres, runs migrations, then starts the API and UI.

---

## System Architecture

```
 ┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐
 │  sebi.gov.in scraper │   │  PDF upload (UI/API) │   │  backend/downloads/  │
 │  app/scraper         │   │  POST /circulars/... │   │  auto-seed on start  │
 └──────────┬───────────┘   └──────────┬───────────┘   └──────────┬───────────┘
            └──────────────────────────┼──────────────────────────┘
                                       ▼
                 ┌─────────────────────────────────────────┐
                 │  app/engine/text.py  (PyMuPDF)          │
                 │  header · addressees · Para refs · page │
                 └────────────────────┬────────────────────┘
                                      ▼
        ┌──────────────────────────────────────────────────────────┐
        │ app/engine/analyzer.py          ◄── app/engine/llm.py    │
        │ obligations · exemptions · deadlines   (optional Claude/ │
        │ applicability · ambiguity · risk        Groq proposals,  │
        │ citation verification                   quote-verified)  │
        └────────────────────────────┬─────────────────────────────┘
                                     ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │ app/engine/service.py — workflow state machine (PostgreSQL)          │
   │ created → in_analysis → GATE 1 → planning → GATE 2 → executing →     │
   │ compliant   (impact map · SOP drafts · tasks · evidence · roll-up)   │
   │ app/engine/audit.py — SHA-256 hash-chained audit_events              │
   └────────────────────────────┬─────────────────────────────────────────┘
                                ▼
                 ┌─────────────────────────────────────────┐
                 │  FastAPI  /api/v2/*   (port 8000)        │
                 └────────────────────┬────────────────────┘
                                      ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │ React + TanStack Start UI (port 5173)                                 │
   │ Dashboard · Inbox · Workspace · Obligations · Impact Map · Plan ·     │
   │ Tracker · Compliance Register · Audit Trail · Onboarding · Settings   │
   └──────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

**Backend**

![Python](https://img.shields.io/badge/Python-1e293b?style=for-the-badge&logo=python&logoColor=3776AB)
![FastAPI](https://img.shields.io/badge/FastAPI-1e293b?style=for-the-badge&logo=fastapi&logoColor=009688)
![Pydantic](https://img.shields.io/badge/Pydantic-1e293b?style=for-the-badge&logo=pydantic&logoColor=E92063)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-1e293b?style=for-the-badge&logo=sqlalchemy&logoColor=D71F00)
![Alembic](https://img.shields.io/badge/Alembic-1e293b?style=for-the-badge&logo=python&logoColor=6BA81E)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-1e293b?style=for-the-badge&logo=postgresql&logoColor=4169E1)
![PyMuPDF](https://img.shields.io/badge/PyMuPDF-1e293b?style=for-the-badge&logo=adobeacrobatreader&logoColor=EC1C24)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-1e293b?style=for-the-badge&logo=python&logoColor=FFD43B)
![Anthropic](https://img.shields.io/badge/Claude_(optional)-1e293b?style=for-the-badge&logo=anthropic&logoColor=D97757)
![Pytest](https://img.shields.io/badge/Pytest-1e293b?style=for-the-badge&logo=pytest&logoColor=0A9EDC)

**Frontend**

![React](https://img.shields.io/badge/React_19-1e293b?style=for-the-badge&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-1e293b?style=for-the-badge&logo=typescript&logoColor=3178C6)
![Vite](https://img.shields.io/badge/Vite-1e293b?style=for-the-badge&logo=vite&logoColor=646CFF)
![TanStack](https://img.shields.io/badge/TanStack_Router_%2B_Query-1e293b?style=for-the-badge&logo=reactquery&logoColor=FF4154)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS_4-1e293b?style=for-the-badge&logo=tailwindcss&logoColor=06B6D4)
![Radix UI](https://img.shields.io/badge/shadcn%2FRadix-1e293b?style=for-the-badge&logo=radixui&logoColor=FFFFFF)

---

## Installation & Quickstart

### Prerequisites

| Tool | Version | Notes |
|---|---|---|
| PostgreSQL | 15+ (tested on 18) | Only the **binaries** (`initdb`, `pg_ctl`, `psql`) are used. SERA runs its own cluster. |
| Python | 3.12 | Python 3.13+ is not supported by the pinned native dependencies. |
| Node.js | 20+ (tested on 22) | Includes `npm` / `npx`. |
| API keys | *none required* | `ANTHROPIC_API_KEY` or `GROQ_API_KEY` are optional. |

### Option A: one click (Windows)

```powershell
git clone https://github.com/sarthakviche/SERA-Securities-Engine-for-Regulatory-Action.git
cd SERA-Securities-Engine-for-Regulatory-Action
.\"Start SERA.cmd"
```

`start-sera.ps1` does the following:
- creates a project-local Postgres cluster in `.localdb/` (port **55432**, user/password `sera`/`sera`, database `sera`);
- creates `backend/.venv` and installs the requirements;
- writes `backend/.env` if it is missing, and runs `alembic upgrade head`;
- starts the API on `:8000` and the UI on `:5173`;
- opens http://localhost:5173.

`.\"Stop SERA.cmd"` stops all three.

### Option B: manual

```powershell
# 1. Database (project-local cluster on port 55432)
"sera" | Out-File -Encoding ascii -NoNewline $env:TEMP\pw.txt
initdb -D .localdb\pgdata -U sera --pwfile=$env:TEMP\pw.txt -A scram-sha-256 -E UTF8 --locale=C
pg_ctl -D .localdb\pgdata -o "-p 55432" -l .localdb\postgres.log start -w
$env:PGPASSWORD = "sera"; psql -h 127.0.0.1 -p 55432 -U sera -d postgres -c "create database sera"

# 2. Backend
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env        # then edit DATABASE_URL (below)
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 3. Frontend (new terminal)
cd frontend
npm install
npx vite dev --port 5173
```

### `backend/.env`

```dotenv
DATABASE_URL=postgresql+asyncpg://sera:sera@127.0.0.1:55432/sera
EMAIL_ENABLED=false            # true + RESEND_API_KEY to send email notifications
FRONTEND_URL=http://localhost:5173
ANTHROPIC_API_KEY=             # optional: Claude proposes obligations, SERA verifies them
GROQ_API_KEY=                  # optional alternative provider
```

The UI talks to the API through Vite's `/api` proxy, so no extra frontend configuration is needed. Interactive API docs are at http://127.0.0.1:8000/docs.

---

## Usage Examples

**Check the engine and organisation profile**

```bash
curl -s http://127.0.0.1:8000/api/v2/meta
```
```json
{
  "provider": "offline",
  "org": {
    "name": "Arthavault Securities Pvt. Ltd.",
    "entity_types": ["stock_broker", "depository_participant", "investment_adviser", "research_analyst"],
    "onboarded": true
  }
}
```
*(trimmed; the response also lists all selectable entity types, default departments and systems)*

**Upload any circular PDF; analysis starts automatically**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v2/circulars/upload \
  -F "file=@backend/downloads/SEBI-CIRC-2026-08-03-103314.pdf" -F "source=SEBI"
```
```json
{ "document_id": "1cdad22e-…", "workflow_id": "700fd938-…", "created": true }
```

**Read the cited result, then approve both gates**

```bash
curl -s http://127.0.0.1:8000/api/v2/workflows/<workflow_id>
curl -s -X POST http://127.0.0.1:8000/api/v2/workflows/<workflow_id>/gate/gate_1 \
  -H "Content-Type: application/json" -d '{"decision":"approved","comment":"Interpretation OK"}'
curl -s -X POST http://127.0.0.1:8000/api/v2/workflows/<workflow_id>/gate/gate_2 \
  -H "Content-Type: application/json" -d '{"decision":"rejected","comment":"Add a UAT step for IT"}'
```
```json
{ "status": "pending_approval_2", "current_stage": "gate_2" }
```

A rejected Gate 2 regenerates the plan and adds `Reviewer request: Add a UAT step for IT`, owned by *IT & Information Security*.

**Submit evidence for a task**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v2/tasks/<task_id>/evidence \
  -F "file=@proof.pdf" -F "note=Accounts re-tagged" -F "complete=true"
```

**Verify the audit chain**

```bash
curl -s http://127.0.0.1:8000/api/v2/audit/verify
```
```json
{ "valid": true, "checked": 15, "head": "865cec80fc92f094c4556ca0321ef328a77314a4a97443b29ea3ffa7bb2a2466" }
```

**Scripts** (run from `backend/` with `.venv\Scripts\python.exe`)

```powershell
.\.venv\Scripts\python.exe scripts\smoke_v2.py           # E2E: analyse → gates → evidence → compliant → verify
.\.venv\Scripts\python.exe scripts\tamper_demo.py        # edit an audit row → chain reports "valid": false
.\.venv\Scripts\python.exe scripts\tamper_demo.py --undo # restore it
.\.venv\Scripts\python.exe scripts\reset_demo.py         # clean demo state, re-register PDFs in downloads/
.\.venv\Scripts\python.exe -m pytest tests\engine -q     # 10 passed
```

Example `smoke_v2.py` output on the PaRRVA circular:

```
after analysis: pending_approval_1 - ... SERA identified 1 requirement(s), 1 applicable to your organisation,
                1 needing interpretation. Earliest applicable deadline: 2026-09-03.
   OB-MIRSD-18038-01 [CRITICAL] APPL Para 2: Investment Advisers / Research Analysts: Enrol with PaRRVA by September 03, 2026 ...
after gate 1: pending_approval_2 | tasks in plan: 4
after gate 2: executing | tasks: 4
final: compliant 100
audit chain: {'valid': True, 'checked': 15, ...}
```

---

## Roadmap

- [x] SEBI circular scraper and PDF downloader
- [x] Paragraph-level PDF parsing with page citations
- [x] Offline obligation, exemption, deadline and SLA extraction
- [x] Org-profile applicability, ambiguity detection and risk scoring
- [x] Optional Claude/Groq proposals with quote verification
- [x] Gate 1 / Gate 2 human approvals with feedback loop
- [x] Impact map, SOP drafts and three-phase implementation plan
- [x] Evidence vault (SHA-256) and compliance roll-up
- [x] Hash-chained audit trail with integrity verification
- [x] Live dashboard, compliance-register CSV export, one-click launcher
- [ ] Local OCR for scanned (image-only) circulars
- [ ] Clause-level diff against SEBI Master Circulars
- [ ] Recurring obligations as a scheduled compliance calendar
- [ ] Multi-user auth with department-scoped RBAC
- [ ] Scheduled SEBI monitoring (replace the empty Celery stubs)
- [ ] RBI, IRDAI and MCA regulator packs

---

## Contributing & License

1. Open an [issue](https://github.com/sarthakviche/SERA-Securities-Engine-for-Regulatory-Action/issues) describing the bug or feature.
2. Fork the repo, then branch from `main` (`feat/<topic>` or `fix/<topic>`).
3. Run `pytest tests/engine` and `scripts/smoke_v2.py` before opening a PR.
4. Open a pull request describing the change and how you tested it.

> This repository is connected to Lovable. Never force-push or rewrite published history.

Licensed under the [MIT License](LICENSE).

---

<div align="center">

**Built by Sarthak Viche**

</div>
