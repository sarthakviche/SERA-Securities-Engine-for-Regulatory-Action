import json
import logging
from typing import List, Dict, Any
from pathlib import Path

from app.ai.llm_client import llm_client
from app.ai.agents.extraction.schemas import SemanticObject
from app.ai.agents.applicability.schemas import ApplicabilityOutput
from app.ai.agents.ambiguity.schemas import AmbiguityOutput
from app.ai.agents.obligation.schemas import ObligationOutput, ExtractedObligation

logger = logging.getLogger(__name__)

class ObligationAgent:
    def __init__(self):
        self.system_prompt = (
            "You are a strict regulatory compliance parser. Your task is to extract and normalize "
            "actionable regulatory obligations from the provided semantic objects. "
            "Only process objects that are deemed applicable based on the applicability assessment. "
            "For each obligation, provide a clear title, category, text, and regulatory reference. "
            "IMPORTANT RULES:\n"
            "1. NEVER invent a deadline, owner, or evidence requirement. If it is not explicitly stated in the text, leave it null.\n"
            "2. Ensure the obligation is strictly derived from the provided regulatory text.\n"
            "3. Do not hallucinate obligations that do not exist."
        )

    async def extract_obligations(self, semantic_objects: List[SemanticObject], applicability: ApplicabilityOutput, ambiguity: AmbiguityOutput) -> ObligationOutput:
        # Filter objects that are actually applicable to reduce prompt size and hallucination risk
        applicable_ids = {
            assessment.object_id 
            for assessment in applicability.object_assessments 
            if assessment.is_applicable
        }
        
        applicable_objects = [obj for obj in semantic_objects if obj.object_id in applicable_ids]
        
        if not applicable_objects:
            return ObligationOutput(obligations=[])
            
        payload = {
            "applicable_semantic_objects": [obj.model_dump() for obj in applicable_objects],
            "ambiguity_context": ambiguity.model_dump()
        }
        
        user_prompt = (
            "Extract normalized actionable obligations from the following applicable semantic objects. "
            "Use the ambiguity context if it helps clarify the requirement.\n\n"
            f"{json.dumps(payload, indent=2)}"
        )
        
        try:
            output = await llm_client.generate_structured(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                response_model=ObligationOutput
            )
            return output
        except Exception as e:
            logger.error(f"Obligation extraction failed: {str(e)}")
            raise

    async def run(self, document_id: str, semantic_objects: List[SemanticObject], applicability: ApplicabilityOutput, ambiguity: AmbiguityOutput, data_dir: Path) -> ObligationOutput:
        """
        Runs the obligation extraction and saves the result.
        """
        if not semantic_objects:
            return ObligationOutput(obligations=[])
            
        output = await self.extract_obligations(semantic_objects, applicability, ambiguity)
        
        # Save output for debugging/pipeline flow
        pipeline_dir = data_dir / "pipeline_output" / document_id
        output_file = pipeline_dir / "obligations.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output.model_dump(), f, indent=2)
            
        return output

obligation_agent = ObligationAgent()
