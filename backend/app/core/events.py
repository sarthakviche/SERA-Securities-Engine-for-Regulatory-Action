"""Domain event publisher interface — TRD §7.2. Real implementation publishes
to Redis Streams (§7.3); this slice ships an in-memory fake so node code can
call the real interface today.

Event names used by this slice's 3 agents:
  - "impact_mapping.completed"   (companion-doc-specific fan-out, not in the
     TRD's own §7.2 table — kept because the companion doc calls it out
     explicitly for an early Notification Service heads-up, independent of
     graph advancement)
  - "workflow.stage_completed"   (TRD §7.2: published by every node, consumed
     by the LangGraph orchestrator to advance the graph)
  - "gate_2.rejected"            (companion doc §7: consumed by Notification
     Service + triggers sop_generation_agent re-entry)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger("sera.events")


class DomainEvent(BaseModel):
    event_type: str
    organization_id: UUID
    workflow_id: UUID | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    idempotency_key: str = Field(default_factory=lambda: str(uuid4()))


class EventPublisher(Protocol):
    async def publish(self, event: DomainEvent) -> None: ...


class InMemoryEventPublisher:
    """Collects every published event (for test assertions) and logs it (for
    demo-script visibility). Real implementation: publish to Redis Streams.
    """

    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        self.published.append(event)
        logger.info("event published: %s workflow=%s payload=%s", event.event_type, event.workflow_id, event.payload)
