import json
import logging
from typing import List, Dict, Any
from pathlib import Path

from app.ai.llm_client import llm_client
from app.ai.agents.extraction.schemas import ExtractionOutput, SemanticObject
from .prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class ExtractionAgent:
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT

    async def extract_batch(self, batch_text: str) -> List[SemanticObject]:
        user_prompt = f"Extract the semantic objects from the following regulatory text:\n\n{batch_text}"
        
        try:
            output = await llm_client.generate_structured(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                response_model=ExtractionOutput
            )
            return output.objects
        except Exception as e:
            logger.error(f"Extraction failed for batch: {str(e)}")
            raise

    async def run(self, document_id: str, data_dir: Path) -> List[SemanticObject]:
        """
        Reads semantic_batches.json, processes each batch, and saves semantic_objects.json.
        """
        pipeline_dir = data_dir / "pipeline_output" / document_id
        batches_file = pipeline_dir / "semantic_batches.json"
        
        if not batches_file.exists():
            raise FileNotFoundError(f"semantic_batches.json not found for document {document_id}")
            
        with open(batches_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        batches = data.get("batches", [])
        if not batches:
            raise ValueError("No batches found in semantic_batches.json")
            
        all_objects = []
        obj_counter = 1
        
        for batch in batches:
            batch_text = batch.get("text", "")
            if not batch_text.strip():
                continue
                
            objects = await self.extract_batch(batch_text)
            
            # Map the clause_ids heuristically if needed, or just let the LLM return it.
            # Assign unique IDs
            for obj in objects:
                obj.object_id = f"obj_{obj_counter}"
                obj_counter += 1
                all_objects.append(obj)
                
        # Save to semantic_objects.json
        output_file = pipeline_dir / "semantic_objects.json"
        output_data = {
            "document_id": document_id,
            "objects": [obj.model_dump() for obj in all_objects]
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
            
        return all_objects

extraction_agent = ExtractionAgent()
