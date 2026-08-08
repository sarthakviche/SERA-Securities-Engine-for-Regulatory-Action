"""Pydantic models mirroring the `workflow_documents` table (TRD §4.2) and the
Shared Workflow Document (SWD) that lives in its `swd JSONB` column.

These are the shared shape every agent node reads/writes through
`workflow.service` — nothing here is specific to the 3 agents in this slice,
so upstream agents (applicability, obligation_extraction, ...) rely on the
same models.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkflowStatus(str, Enum):
    """Coarse lifecycle status (TRD §4.2 `workflow_documents.status`).

    "planning" covers both the `sop_generation` and `evidence_implementation_plan`
    stages that replaced the TRD's original single `planning_agent` node
    (see sera_three_agents_workflow_and_plan.md) — which sub-stage is active
    is carried by `WorkflowDocument.current_stage`, not a new status value.
    """

    created = "created"
    in_analysis = "in_analysis"
    pending_approval_1 = "pending_approval_1"
    impact_mapping = "impact_mapping"
    planning = "planning"
    pending_approval_2 = "pending_approval_2"
    executing = "executing"
    monitoring = "monitoring"
    archived = "archived"


class GateDecision(str, Enum):
    approved = "approved"
    rejected = "rejected"


class GateApproval(BaseModel):
    decision: GateDecision
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    comment: str | None = None  # rejection feedback, e.g. gate_2 loop-back


class ExecutionHistoryEntry(BaseModel):
    agent_name: str
    timestamp: datetime
    status: str  # "completed" | "failed" | "needs_human"
    detail: str | None = None


class AgentTask(BaseModel):
    """A human-review item raised by an agent instead of guessing.

    Backs the TRD's `GET /workflows/{id}/tasks` (agent_tasks projection) and
    `POST /workflows/{id}/agent-tasks/{task_id}/resolve` endpoints — those
    aren't implemented in this slice (no API layer), but this is the shape
    they'll eventually read/write.
    """

    id: UUID
    raised_by_agent: str
    reason: str
    context: dict[str, Any] = Field(default_factory=dict)
    resolved: bool = False
    resolution: dict[str, Any] | None = None
    created_at: datetime


class SWDPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_metadata: dict[str, Any] = Field(default_factory=dict)
    agent_outputs: dict[str, Any] = Field(default_factory=dict)
    human_approvals: dict[str, GateApproval] = Field(default_factory=dict)
    execution_history: list[ExecutionHistoryEntry] = Field(default_factory=list)
    agent_tasks: list[AgentTask] = Field(default_factory=list)


class WorkflowDocument(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    organization_id: UUID
    status: WorkflowStatus
    current_stage: str
    swd: SWDPayload
    schema_version: int = 1
