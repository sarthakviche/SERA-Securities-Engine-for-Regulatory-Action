# SERA backend — impact_mapping / sop_generation / evidence_implementation_plan slice

This covers only the `feature/Mapping_Agents` slice: `impact_mapping_agent`,
`sop_generation_agent`, `evidence_implementation_plan_agent`, `human_gate_2`,
`execution_handoff`, and the shared plumbing they need to run
(`modules/workflow`, `modules/obligations`, `modules/tasks`, `modules/audit`,
`modules/knowledge/*`, `ai/providers`, `ai/graph/*`). See `SERA_TRD.md` at
the repo root for the full system spec, and
`sera_three_agents_workflow_and_plan.md` for this slice's own delta spec.

## Setup

```bash
cd backend
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -e ".[dev]"   # Windows
# source .venv/bin/activate && pip install -e ".[dev]"  # macOS/Linux
cp .env.example .env   # then fill in ANTHROPIC_API_KEY
```

## Running tests

```bash
./.venv/Scripts/python.exe -m pytest -v
```

27 tests: unit tests per node/helper (mocked LLM, no network calls) plus
integration tests running the full compiled LangGraph graph — including a
real `interrupt()`/`Command(resume=...)` pause-and-resume cycle at `gate_2`,
and both the approve→materialize and reject→loop-back paths.

## Running the demo

Requires a real `ANTHROPIC_API_KEY` (makes live Claude Sonnet 5 calls):

```bash
./.venv/Scripts/python.exe scripts/run_demo.py
```

Seeds a fixture circular, runs `impact_mapping -> sop_generation ->
evidence_implementation_plan`, prints each agent's output, auto-approves
`gate_2`, then prints the materialized `org_sops`/`tasks`/`audit_log` rows.

## Architecture note: everything here is a swappable fake

Real Postgres/pgvector/Redis are out of scope for this slice — `core/db.py`
is untouched. Every piece of persistence this slice needs is an in-memory
implementation of a `Protocol` a teammate can implement for real without
touching any agent/graph code:

| Protocol | Fake here | Real implementation | Hard requirement |
|---|---|---|---|
| `WorkflowRepository` (`modules/workflow/repository.py`) | `InMemoryWorkflowRepository` | SQLAlchemy-backed, real `workflow_documents` table (TRD §4.2) | Preserve merge-not-replace semantics for `agent_outputs`/`human_approvals` in `update_swd_fields`. |
| `ObligationRepository` / `TaskRepository` / `AuditRepository` | In-memory, backed by the shared `InMemoryOrgStore` (`adapters/memory/store.py`) | Real Postgres repositories per TRD §4.2 DDL | `execution_handoff`'s transaction (`InMemoryOrgStore.begin()`) must become a real DB transaction — its fail-closed guarantee depends on rollback-on-exception actually happening at the DB level. |
| `OrganizationalRepository` (`modules/knowledge/organizational/repository.py`) | In-memory | Real Postgres reads over `org_departments`/`org_systems`/`org_sops` | — |
| `RetrievalProvider` (`modules/knowledge/retrieval_provider.py`) | Keyword-overlap fake | pgvector-backed, per TRD §5.4/§5 | Must implement both `search_regulatory` and `search_organizational` (incl. the `department_ids` filter extension `sop_generation_agent` relies on). |
| `EventPublisher` (`core/events.py`) | In-memory list + log | Redis Streams, per TRD §7.2/§7.3 | Reuse the event-name strings already used in node code. |
| `checkpointer.get_checkpointer()` | `MemorySaver()` | `AsyncPostgresSaver(DATABASE_URL)` (`langgraph-checkpoint-postgres`) | One-line swap, per TRD §8.4. |

**Single seam**: `app/ai/graph/deps.py` — `build_deps()` is the only place
any concrete adapter class gets constructed. Everything else (nodes,
`build_graph.py`, tests) only ever type-hints against the `Protocol`s above.

## What's NOT in this slice

- `applicability_agent.py`, `obligation_extraction_agent.py`,
  `change_analysis_agent.py`, `ambiguity_detection_agent.py`, `human_gate_1`
  — other agents' implementers. `build_graph.py` has a commented TODO block
  showing exactly how to wire them in once they exist.
- No HTTP API layer (`main.py`, `modules/workflow/router.py` untouched) —
  proven via `scripts/run_demo.py` and pytest only.
- No real DB/Redis/S3 — see the table above.
