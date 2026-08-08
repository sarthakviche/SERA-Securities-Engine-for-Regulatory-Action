"""Structured output schema for evidence_implementation_plan_agent.

Per sera_three_agents_workflow_and_plan.md §5. This is the direct precursor
to `tasks` table rows (TRD §4.2) — nothing is inserted until execution_handoff
runs on gate_2 approval; until then it's a proposal living in the SWD.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class ProposedTask(BaseModel):
    title: str
    description: str
    owner_department_id: UUID | None
    suggested_assignee_id: UUID | None
    due_date_rule: str  # e.g. "T+30d from gate_2 approval"
    recurrence_rule: str | None  # RRULE, carried from obligation.frequency
    evidence_requirement: str
    priority: Literal["low", "medium", "high"]


class ObligationPlan(BaseModel):
    obligation_id: UUID
    tasks: list[ProposedTask]


class ImplementationPlanOutput(BaseModel):
    plans: list[ObligationPlan]
