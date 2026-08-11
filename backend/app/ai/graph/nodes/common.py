"""Shared scaffold for the node contract (TRD §8.2), reused by all 3 agents
in this slice.

`generate_structured_or_flag` wraps `LLMProvider.generate_structured`: on
`StructuredGenerationError` (retries exhausted per TRD §8.5, or a refusal),
it records an `AgentTask` + a "needs_human" execution_history entry and
raises `NodeNeedsHumanReviewError` instead of letting the exception escape
raw — LangGraph's Postgres/Memory checkpointer (checkpointer.py) resumes
from the last successful checkpoint on any node failure (TRD §8.4), so
raising here is safe: nothing partial is left in the SWD for this agent's
own output key.
"""

from __future__ import annotations

from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel

from app.ai.graph.deps import NodeDeps
from app.ai.providers.llm_provider import StructuredGenerationError

T = TypeVar("T", bound=BaseModel)


class NodeNeedsHumanReviewError(Exception):
    def __init__(self, agent_name: str, workflow_id: UUID, reason: str) -> None:
        super().__init__(f"{agent_name} needs human review for workflow {workflow_id}: {reason}")
        self.agent_name = agent_name
        self.workflow_id = workflow_id
        self.reason = reason


async def generate_structured_or_flag(
    *,
    deps: NodeDeps,
    workflow_id: UUID,
    agent_name: str,
    system_prompt: str,
    user_prompt: str,
    response_schema: type[T],
) -> T:
    try:
        return await deps.llm_provider.generate_structured(
            system_prompt=system_prompt, user_prompt=user_prompt, response_schema=response_schema
        )
    except StructuredGenerationError as exc:
        await deps.workflow_service.append_execution_history(
            workflow_id, agent_name, "needs_human", detail=str(exc)
        )
        await deps.workflow_service.add_agent_task(
            workflow_id,
            raised_by_agent=agent_name,
            reason=f"LLM structured generation failed after retries: {exc}",
            context={"last_raw_input": exc.last_raw_input},
        )
        raise NodeNeedsHumanReviewError(agent_name, workflow_id, str(exc)) from exc
