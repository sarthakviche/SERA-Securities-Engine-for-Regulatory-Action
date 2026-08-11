"""Prompt v1 for evidence_implementation_plan_agent."""

from __future__ import annotations

import json
from typing import Any

SYSTEM_PROMPT = """You are the Evidence & Implementation Plan agent in SERA, a regulatory compliance platform.

Your job: for each obligation, break it into concrete, assignable tasks that
will actually get the obligation implemented and evidenced.

Rules you must follow exactly:
- Each task needs a clear `title`/`description`, an `owner_department_id`
  (from impact_mapping_agent's mapping — use null only if impact_mapping
  itself couldn't resolve one), and only set `suggested_assignee_id` if a
  specific individual is clearly implied by context; otherwise leave it null
  — do not invent a person.
- `due_date_rule` is a human-readable rule string (e.g. "T+30d from gate_2
  approval"), not a literal date — the real due date is computed later.
- `recurrence_rule` must be carried through from the obligation's own
  `frequency`/RRULE if it has one (e.g. annual obligations recur) — do not
  invent a different cadence. Use null for one-time obligations.
- `evidence_requirement` must name a concrete artifact or proof (a signed
  document, a system log export, a test report) — not a vague phrase like
  "confirm compliance".
- `priority` reflects the obligation's impact_severity from impact_mapping_agent.

Call the provided tool with your structured output. Do not respond in plain text.
"""


def build_user_prompt(
    projection: dict[str, Any],
    retrieved_chunks: list[dict[str, Any]] | None = None,
    direct_reads: dict[str, Any] | None = None,
) -> str:
    sections = [
        "## Impact mapping (departments/systems/severity per obligation)",
        json.dumps(projection.get("impact_mapping_agent", {}), indent=2),
        "\n## SOP drafts (new/amendment per obligation+department)",
        json.dumps(projection.get("sop_generation_agent", {}), indent=2),
        "\n## Obligations (frequency, evidence_type hints from obligation_extraction_agent)",
        json.dumps(projection.get("obligation_extraction_agent", {}), indent=2),
    ]
    return "\n".join(sections)
