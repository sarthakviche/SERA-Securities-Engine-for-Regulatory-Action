import pytest
import json
from pathlib import Path
from unittest.mock import patch, AsyncMock
from app.ai.agents.extraction.agent import ExtractionAgent
from app.ai.agents.extraction.schemas import ExtractionOutput, SemanticObject

@pytest.fixture
def mock_semantic_batches(tmp_path):
    pipeline_dir = tmp_path / "pipeline_output" / "test_doc"
    pipeline_dir.mkdir(parents=True)
    batches_file = pipeline_dir / "semantic_batches.json"
    
    mock_data = {
        "document_path": "test.pdf",
        "batches": [
            {"batch_id": "b_1", "text": "This is a test obligation."}
        ]
    }
    
    with open(batches_file, "w") as f:
        json.dump(mock_data, f)
        
    return tmp_path

@pytest.mark.asyncio
@patch("app.ai.agents.extraction.agent.llm_client.generate_structured")
async def test_extraction_agent(mock_generate, mock_semantic_batches):
    agent = ExtractionAgent()
    
    mock_generate.return_value = ExtractionOutput(
        objects=[
            SemanticObject(
                object_id="obj_mock",
                type="obligation",
                text="Test obligation extracted",
                context="Test Context"
            )
        ]
    )
    
    results = await agent.run("test_doc", mock_semantic_batches)
    
    assert len(results) == 1
    assert results[0].type == "obligation"
    assert results[0].object_id == "obj_1"  # Agent rewrites IDs
    
    # Check that output was saved
    output_file = mock_semantic_batches / "pipeline_output" / "test_doc" / "semantic_objects.json"
    assert output_file.exists()
    
    with open(output_file, "r") as f:
        saved_data = json.load(f)
        assert len(saved_data["objects"]) == 1
        assert saved_data["objects"][0]["object_id"] == "obj_1"
