import pytest
import json
from pathlib import Path
from unittest.mock import patch, AsyncMock
from app.ai.agents.applicability.agent import ApplicabilityAgent
from app.ai.agents.applicability.schemas import ApplicabilityOutput, ObjectApplicability
from app.ai.agents.extraction.schemas import SemanticObject

@pytest.fixture
def mock_pipeline_dir(tmp_path):
    pipeline_dir = tmp_path / "pipeline_output" / "test_doc"
    pipeline_dir.mkdir(parents=True)
    return tmp_path

@pytest.mark.asyncio
@patch("app.ai.agents.applicability.agent.llm_client.generate_structured")
async def test_applicability_agent(mock_generate, mock_pipeline_dir):
    agent = ApplicabilityAgent()
    
    semantic_objects = [
        SemanticObject(
            object_id="obj_1",
            type="obligation",
            text="IAs must enroll with PaRRVA",
            context="Clause 1"
        )
    ]
    
    mock_generate.return_value = ApplicabilityOutput(
        overall_applicability_score=0.9,
        overall_reasoning="Mention of IAs makes it highly applicable.",
        object_assessments=[
            ObjectApplicability(
                object_id="obj_1",
                is_applicable=True,
                reasoning="Explicitly targets Investment Advisers",
                confidence_score=0.95
            )
        ]
    )
    
    result = await agent.run("test_doc", semantic_objects, mock_pipeline_dir)
    
    assert result.overall_applicability_score == 0.9
    assert len(result.object_assessments) == 1
    assert result.object_assessments[0].is_applicable is True
    
    output_file = mock_pipeline_dir / "pipeline_output" / "test_doc" / "applicability_assessment.json"
    assert output_file.exists()
    
    with open(output_file, "r") as f:
        saved_data = json.load(f)
        assert saved_data["overall_applicability_score"] == 0.9
