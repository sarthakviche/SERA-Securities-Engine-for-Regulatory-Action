"""Structured output schema for impact_mapping_agent.

Per sera_three_agents_workflow_and_plan.md §5. `department_id: None` is a
valid, schema-conforming value — it signals "no confident match", which the
node routes to an AgentTask for human resolution (fail closed) rather than
guessing.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class DepartmentImpact(BaseModel):
    department_id: UUID | None
    department_name_suggested: str
    role: Literal["primary_owner", "contributor", "informed"]


class ObligationImpact(BaseModel):
    obligation_id: UUID
    affected_departments: list[DepartmentImpact]
    affected_systems: list[str]
    impact_severity: Literal["low", "medium", "high", "critical"]
    dependencies: list[UUID]
    rationale: str
    confidence: float


class ImpactMappingOutput(BaseModel):
    mappings: list[ObligationImpact]
