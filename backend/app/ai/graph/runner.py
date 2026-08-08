import asyncio
from uuid import UUID
from typing import Optional

from langgraph.types import Command
from app.ai.graph.build_graph import build_graph
from app.ai.graph.deps import build_deps
from app.ai.graph.state import WorkflowState
from app.adapters.memory.store import InMemoryOrgStore, ObligationRow
from app.modules.workflow.schemas import WorkflowDocument
from app.core.db import AsyncSessionLocal
from app.modules.workflow.repository import workflow_repository

async def _seed_deps_from_swd(deps, workflow_id: UUID):
    """
    Reads the SWD from Postgres and seeds the in-memory OrgStore obligations
    so that impact_mapping_agent has the initial obligations.
    """
    async with AsyncSessionLocal() as db:
        wf = await workflow_repository.get_workflow(db, workflow_id)
        if wf and wf.swd and isinstance(wf.swd, dict):
            agent_outputs = wf.swd.get("agent_outputs", {})
            ob_out = agent_outputs.get("obligation_extraction_agent", {})
            obligations = ob_out.get("obligations", [])
            for ob in obligations:
                deps.org_store.tables.obligations.append(
                    ObligationRow(
                        id=UUID(ob.get("id")) if ob.get("id") else UUID(int=0),
                        workflow_id=workflow_id,
                        organization_id=wf.organization_id,
                        description=ob.get("description", ""),
                        status="proposed",
                    )
                )

async def invoke_graph(workflow_id: UUID, organization_id: UUID) -> None:
    """Fire-and-forget: called after Gate 1 approval."""
    async with AsyncSessionLocal() as db:
        store = InMemoryOrgStore()
        deps = build_deps(store=store, db_session=db)
        
        # Seed the store from the SQL-backed SWD
        await _seed_deps_from_swd(deps, workflow_id)
        
        graph = build_graph(deps)
        config = {"configurable": {"thread_id": str(workflow_id)}}
        state = WorkflowState(workflow_id=workflow_id)
        
        await graph.ainvoke(state, config=config)

async def resume_graph(workflow_id: UUID, gate_name: str, decision: str, comment: Optional[str]) -> None:
    """Resume after a gate decision (used for Gate 2)."""
    # For prototype, we re-instantiate empty store because execution_handoff
    # will push the real rows into it. A fully mature system would persist
    # the store state or re-hydrate it.
    async with AsyncSessionLocal() as db:
        store = InMemoryOrgStore()
        deps = build_deps(store=store, db_session=db)
        
        graph = build_graph(deps)
        config = {"configurable": {"thread_id": str(workflow_id)}}
        
        await graph.ainvoke(
            None,
            config=config,
            command=Command(resume={"decision": decision, "comment": comment, "approved_by": None}),
        )
