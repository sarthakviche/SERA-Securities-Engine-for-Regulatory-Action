"""The single DI seam for this slice (feature/Mapping_Agents).

Every concrete adapter class (`InMemory*`, `AnthropicLLMProvider`) is
constructed HERE and nowhere else. Node code, `build_graph.py`, tests, and
the demo script only ever type-hint against the Protocols in
`modules/*/repository.py`, `modules/knowledge/retrieval_provider.py`,
`core/events.py`, and `ai/providers/llm_provider.py`.

There's no FastAPI `Depends()` wiring here (per plan decision: no API layer
in this slice) — `build_deps()` is a plain factory. A teammate adding the
real Postgres/Redis-backed implementations only needs to change the bodies
of this file; nothing that imports `NodeDeps` needs to change.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.memory.store import InMemoryOrgStore
from app.ai.providers.llm_provider import AnthropicLLMProvider, LLMProvider
from app.core.config import Settings, get_settings
from app.core.events import EventPublisher, InMemoryEventPublisher
from app.core.notification_event_publisher import NotificationAwareEventPublisher
from app.modules.audit.repository import AuditRepository, InMemoryAuditRepository
from app.modules.knowledge.organizational.repository import (
    InMemoryOrganizationalRepository,
    OrganizationalRepository,
)
from app.modules.knowledge.retrieval_provider import InMemoryRetrievalProvider, RetrievalProvider
from app.modules.obligations.repository import InMemoryObligationRepository, ObligationRepository
from app.modules.tasks.repository import InMemoryTaskRepository, TaskRepository
from app.modules.workflow.repository import InMemoryWorkflowRepository, WorkflowRepository
from app.modules.workflow.service import AgentWorkflowService


@dataclass
class NodeDeps:
    workflow_service: AgentWorkflowService
    organizational_repo: OrganizationalRepository
    obligation_repo: ObligationRepository
    task_repo: TaskRepository
    audit_repo: AuditRepository
    retrieval_provider: RetrievalProvider
    event_publisher: EventPublisher
    llm_provider: LLMProvider
    org_store: InMemoryOrgStore  # execution_handoff needs this directly to begin a transaction


def build_deps(
    *,
    store: InMemoryOrgStore,
    db_session: AsyncSession | None = None,
    workflow_repository: WorkflowRepository | None = None,
    event_publisher: EventPublisher | None = None,
    llm_provider: LLMProvider | None = None,
    settings: Settings | None = None,
) -> NodeDeps:
    settings = settings or get_settings()
    
    if db_session:
        from app.modules.workflow.repository_sql import SQLAlchemyWorkflowRepository
        workflow_repository = SQLAlchemyWorkflowRepository(db_session)
        # Use the real notification-aware publisher when a DB session is available
        event_publisher = event_publisher or NotificationAwareEventPublisher(db_session)
    else:
        workflow_repository = workflow_repository or InMemoryWorkflowRepository()
        # Tests inject InMemoryEventPublisher directly; fall back to it here
        event_publisher = event_publisher or InMemoryEventPublisher()

    return NodeDeps(
        workflow_service=AgentWorkflowService(workflow_repository),
        organizational_repo=InMemoryOrganizationalRepository(store),
        obligation_repo=InMemoryObligationRepository(store),
        task_repo=InMemoryTaskRepository(store),
        audit_repo=InMemoryAuditRepository(store),
        retrieval_provider=InMemoryRetrievalProvider(store),
        event_publisher=event_publisher,
        llm_provider=llm_provider or AnthropicLLMProvider(settings),
        org_store=store,
    )
