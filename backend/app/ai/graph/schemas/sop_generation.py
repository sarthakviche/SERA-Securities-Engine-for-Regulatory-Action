"""Structured output schema for sop_generation_agent.

Per sera_three_agents_workflow_and_plan.md §5. `content` is a structured
draft rendered as text (title/steps/control points/evidence checkpoints) —
free text lives inside this validated field, it never drives control flow
itself (TRD §1 principle 3). Low-confidence drafts are still written; gate_2
sees `confidence` rather than the draft being blocked.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class SOPDraft(BaseModel):
    obligation_ids: list[UUID]
    department_id: UUID | None
    title: str
    content: str
    based_on_existing_sop_id: UUID | None
    change_type: Literal["new", "amendment"]
    diff_summary: str | None
    confidence: float


class SOPGenerationOutput(BaseModel):
    sop_drafts: list[SOPDraft]
