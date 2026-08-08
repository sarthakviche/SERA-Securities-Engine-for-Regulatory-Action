"""Demo runner for the impact_mapping / sop_generation / evidence_implementation_plan
slice (feature/Mapping_Agents). Seeds the in-memory fakes with a fixture
circular, runs the compiled graph with REAL Claude Sonnet 5 calls
(requires ANTHROPIC_API_KEY), auto-approves gate_2 for demo purposes, and
prints the resulting SWD + materialized rows.

Usage:
    cd backend
    ANTHROPIC_API_KEY=sk-... ./.venv/Scripts/python.exe scripts/run_demo.py
"""

from __future__ import annotations

import asyncio
import json
import sys

from langgraph.types import Command

from app.adapters.memory.seed_data import DOCUMENT_ID, ORGANIZATION_ID, WORKFLOW_ID, build_seed_swd_dict, build_store
from app.ai.graph.build_graph import build_graph
from app.ai.graph.deps import build_deps
from app.ai.graph.state import WorkflowState
from app.core.config import get_settings
from app.modules.workflow.repository import InMemoryWorkflowRepository
from app.modules.workflow.schemas import SWDPayload, WorkflowDocument, WorkflowStatus


async def main() -> None:
    settings = get_settings()
    if not settings.anthropic_api_key:
        print("ANTHROPIC_API_KEY is not set — export it before running this demo.", file=sys.stderr)
        raise SystemExit(1)

    store = build_store()
    workflow_repo = InMemoryWorkflowRepository()
    workflow_repo.seed(
        WorkflowDocument(
            id=WORKFLOW_ID,
            document_id=DOCUMENT_ID,
            organization_id=ORGANIZATION_ID,
            status=WorkflowStatus.pending_approval_1,
            current_stage="gate_1",
            swd=SWDPayload(**build_seed_swd_dict()),
        )
    )
    deps = build_deps(store=store, workflow_repository=workflow_repo, settings=settings)
    graph = build_graph(deps)
    config = {"configurable": {"thread_id": str(WORKFLOW_ID)}}

    print(f"--- Running impact_mapping -> sop_generation -> evidence_implementation_plan for workflow {WORKFLOW_ID} ---")
    paused = await graph.ainvoke(WorkflowState(workflow_id=WORKFLOW_ID), config=config)

    document = await deps.workflow_service.get_document(WORKFLOW_ID)
    print("\n=== impact_mapping_agent output ===")
    print(json.dumps(document.swd.agent_outputs.get("impact_mapping_agent"), indent=2))
    print("\n=== sop_generation_agent output ===")
    print(json.dumps(document.swd.agent_outputs.get("sop_generation_agent"), indent=2))
    print("\n=== evidence_implementation_plan_agent output ===")
    print(json.dumps(document.swd.agent_outputs.get("evidence_implementation_plan_agent"), indent=2))

    if "__interrupt__" not in paused:
        print("\nGraph did not pause at gate_2 as expected — check node wiring.", file=sys.stderr)
        return

    print("\n--- Auto-approving gate_2 for demo purposes ---")
    await graph.ainvoke(Command(resume={"decision": "approved", "approved_by": None}), config=config)

    document = await deps.workflow_service.get_document(WORKFLOW_ID)
    print(f"\nFinal status: {document.status.value}, stage: {document.current_stage}")
    print(f"org_sops rows: {len(store.tables.sops)}")
    print(f"tasks rows: {len(store.tables.tasks)}")
    print(f"audit_log rows: {len(store.tables.audit_log)}")
    print(f"agent_tasks raised for human review: {len(document.swd.agent_tasks)}")


if __name__ == "__main__":
    asyncio.run(main())
