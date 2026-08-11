"""Minimal LangGraph state (TRD §8.1 `WorkflowState`).

Deliberately just `workflow_id` — the real state (SWD, status, current_stage)
lives entirely in the `WorkflowRepository`/`workflow_documents` table, so
there's no second source of truth to keep in sync between the graph and
Postgres. `.advance()` is a no-op passthrough kept for parity with the TRD's
`return state.advance()` pseudocode (TRD §8.2) — the actual stage transition
is already persisted via `workflow_service` before a node returns.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass
class WorkflowState:
    workflow_id: UUID

    def advance(self) -> "WorkflowState":
        return self
