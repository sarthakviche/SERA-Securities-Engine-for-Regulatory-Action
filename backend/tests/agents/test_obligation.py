import pytest
import json
from pathlib import Path
from unittest.mock import patch
from app.ai.agents.obligation.agent import ObligationAgent
from app.ai.agents.obligation.schemas import ObligationOutput, ExtractedObligation
from app.ai.agents.ambiguity.schemas import AmbiguityOutput, ObjectAmbiguity
from app.ai.agents.applicability.schemas import ApplicabilityOutput, ObjectApplicability
from app.ai.agents.extraction.schemas import SemanticObject

@pytest.fixture
def mock_pipeline_dir(tmp_path):
    pipeline_dir = tmp_path / "pipeline_output" / "test_doc"
    pipeline_dir.mkdir(parents=True)
    return tmp_path

@pytest.mark.asyncio
@patch("app.ai.agents.obligation.agent.llm_client.generate_structured")
async def test_obligation_agent(mock_generate, mock_pipeline_dir):
    agent = ObligationAgent()
    
    semantic_objects = [
        SemanticObject(
            object_id="obj_1",
            type="obligation",
            text="IAs must enroll with PaRRVA within three months of its operationalization.",
            context="Clause 1"
        ),
        SemanticObject(
            object_id="obj_2",
            type="obligation",
            text="Stock brokers must report daily margins.",
            context="Clause 2"
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
            ),
            ObjectApplicability(
                object_id="obj_2",
                is_applicable=False, # Should be filtered out
                reasoning="Targets stock brokers",
                confidence_score=1.0
            )
        ]
    )
    
    ambiguity = AmbiguityOutput(
        document_has_ambiguity=False,
        overall_explanation="Clear document",
        object_assessments=[]
    )
    
    mock_generate.return_value = ObligationOutput(
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
    
    result = await agent.run("test_doc", semantic_objects, applicability, ambiguity, mock_pipeline_dir)
    
    assert len(result.obligations) == 1
    assert result.obligations[0].title == "Enroll with PaRRVA"
    assert result.obligations[0].object_id == "obj_1"
    
    output_file = mock_pipeline_dir / "pipeline_output" / "test_doc" / "obligations.json"
    assert output_file.exists()
    
    with open(output_file, "r") as f:
        saved_data = json.load(f)
        assert len(saved_data["obligations"]) == 1
        assert saved_data["obligations"][0]["category"] == "Registration"
