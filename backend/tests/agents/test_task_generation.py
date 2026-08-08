import pytest
import json
from pathlib import Path
from unittest.mock import patch
from app.ai.agents.task_generation.agent import TaskGenerationAgent
from app.ai.agents.task_generation.schemas import TaskGenerationOutput, GeneratedTask
from app.ai.agents.obligation.schemas import ObligationOutput, ExtractedObligation

@pytest.fixture
def mock_pipeline_dir(tmp_path):
    pipeline_dir = tmp_path / "pipeline_output" / "test_doc"
    pipeline_dir.mkdir(parents=True)
    return tmp_path

@pytest.mark.asyncio
@patch("app.ai.agents.task_generation.agent.llm_client.generate_structured")
async def test_task_generation_agent(mock_generate, mock_pipeline_dir):
    agent = TaskGenerationAgent()
    
    obligations = ObligationOutput(
        obligations=[
            ExtractedObligation(
                object_id="obj_1",
                title="Enroll with PaRRVA",
                obligation_text="IAs must enroll with PaRRVA within three months of its operationalization.",
                category="Registration",
                regulatory_reference="Clause 1",
                confidence_score=0.95
            )
        ]
    )
    
    mock_generate.return_value = TaskGenerationOutput(
        tasks=[
            GeneratedTask(
                source_obligation_id="obj_1",
                title="Register IA with PaRRVA",
                description="Complete the enrollment process for the Investment Adviser with PaRRVA within the required timeframe.",
                priority="High",
                owner_role="Compliance Officer",
                deadline="Three months post-operationalization",
                required_evidence="Enrollment confirmation receipt"
            )
        ]
    )
    
    result = await agent.run("test_doc", obligations, mock_pipeline_dir)
    
    assert len(result.tasks) == 1
    assert result.tasks[0].title == "Register IA with PaRRVA"
    assert result.tasks[0].source_obligation_id == "obj_1"
    
    output_file = mock_pipeline_dir / "pipeline_output" / "test_doc" / "tasks.json"
    assert output_file.exists()
    
    with open(output_file, "r") as f:
        saved_data = json.load(f)
        assert len(saved_data["tasks"]) == 1
        assert saved_data["tasks"][0]["priority"] == "High"
