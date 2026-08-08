import pytest
import json
from pathlib import Path
from unittest.mock import patch
from app.ai.agents.ambiguity.agent import AmbiguityAgent
from app.ai.agents.ambiguity.schemas import AmbiguityOutput, ObjectAmbiguity
from app.ai.agents.applicability.schemas import ApplicabilityOutput, ObjectApplicability
from app.ai.agents.extraction.schemas import SemanticObject

@pytest.fixture
def mock_pipeline_dir(tmp_path):
    pipeline_dir = tmp_path / "pipeline_output" / "test_doc"
    pipeline_dir.mkdir(parents=True)
    return tmp_path

@pytest.mark.asyncio
@patch("app.ai.agents.ambiguity.agent.llm_client.generate_structured")
async def test_ambiguity_agent(mock_generate, mock_pipeline_dir):
    agent = AmbiguityAgent()
    
    semantic_objects = [
        SemanticObject(
            object_id="obj_1",
            type="obligation",
            text="IAs must enroll with PaRRVA within three months of its operationalization.",
            context="Clause 1"
        )
    ]
    
    applicability = ApplicabilityOutput(
        overall_applicability_score=0.9,
        overall_reasoning="Applicable to IAs",
        object_assessments=[
            ObjectApplicability(
                object_id="obj_1",
                is_applicable=True,
                reasoning="Targets IAs",
                confidence_score=1.0
            )
        ]
    )
    
    mock_generate.return_value = AmbiguityOutput(
        document_has_ambiguity=True,
        overall_explanation="The phrase 'within three months' is clear, but 'operationalization' may lack a specific date.",
        object_assessments=[
            ObjectAmbiguity(
                object_id="obj_1",
                has_ambiguity=True,
                ambiguity_type="unclear deadline",
                explanation="'operationalization' date is not explicitly defined in this clause.",
                confidence_score=0.8
            )
        ]
    )
    
    result = await agent.run("test_doc", semantic_objects, applicability, mock_pipeline_dir)
    
    assert result.document_has_ambiguity is True
    assert len(result.object_assessments) == 1
    assert result.object_assessments[0].has_ambiguity is True
    assert result.object_assessments[0].ambiguity_type == "unclear deadline"
    
    output_file = mock_pipeline_dir / "pipeline_output" / "test_doc" / "ambiguity_assessment.json"
    assert output_file.exists()
    
    with open(output_file, "r") as f:
        saved_data = json.load(f)
        assert saved_data["document_has_ambiguity"] is True
        assert saved_data["object_assessments"][0]["ambiguity_type"] == "unclear deadline"
