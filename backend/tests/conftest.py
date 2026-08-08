from __future__ import annotations

import pytest

from app.adapters.memory.seed_data import (
    DOCUMENT_ID,
    ORGANIZATION_ID,
    WORKFLOW_ID,
    build_seed_swd_dict,
    build_store,
)
from app.ai.graph.deps import build_deps
from app.modules.workflow.repository import InMemoryWorkflowRepository
from app.modules.workflow.schemas import SWDPayload, WorkflowDocument, WorkflowStatus


@pytest.fixture
def store():
    return build_store()


@pytest.fixture
def seeded_workflow_repo():
    repo = InMemoryWorkflowRepository()
    document = WorkflowDocument(
        id=WORKFLOW_ID,
        document_id=DOCUMENT_ID,
        organization_id=ORGANIZATION_ID,
        status=WorkflowStatus.pending_approval_1,
        current_stage="gate_1",
        swd=SWDPayload(**build_seed_swd_dict()),
    )
    repo.seed(document)
    return repo


@pytest.fixture
def deps(store, seeded_workflow_repo, fake_llm_provider):
    return build_deps(store=store, workflow_repository=seeded_workflow_repo, llm_provider=fake_llm_provider)


@pytest.fixture
def fake_llm_provider():
    """Overridden per-test via a fixture with the same name in the test
    module, or used directly when a test wants to assert on calls.
    """

    class _RecordingFakeLLM:
        def __init__(self) -> None:
            self.calls: list[dict] = []
            self.responses: list[object] = []

        def queue(self, response: object) -> None:
            self.responses.append(response)

        async def generate_structured(self, *, system_prompt, user_prompt, response_schema, max_retries=2):
            self.calls.append(
                {"system_prompt": system_prompt, "user_prompt": user_prompt, "response_schema": response_schema}
            )
            if not self.responses:
                raise AssertionError("fake_llm_provider: no queued response for this call")
            return self.responses.pop(0)

    return _RecordingFakeLLM()
