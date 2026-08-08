import json
import logging
from typing import List, Dict, Any
from pathlib import Path

from app.ai.llm_client import llm_client
from app.ai.agents.extraction.schemas import SemanticObject
from app.ai.agents.applicability.schemas import ApplicabilityOutput, ObjectApplicability

logger = logging.getLogger(__name__)

class ApplicabilityAgent:
    def __init__(self):
        self.system_prompt = (
            "You are a regulatory compliance expert. Your task is to determine if the provided "
            "semantic regulatory objects apply to a specific target organization. "
            "The target organization is an 'Investment Adviser (IA) / Research Analyst (RA)'. "
            "Evaluate each semantic object carefully against this organization profile. "
            "Return a structured applicability assessment."
        )

    async def assess_applicability(self, semantic_objects: List[SemanticObject]) -> ApplicabilityOutput:
        objects_json = json.dumps([obj.model_dump() for obj in semantic_objects], indent=2)
        user_prompt = (
            "Determine the applicability of the following regulatory semantic objects to an "
            "Investment Adviser (IA) / Research Analyst (RA):\n\n"
            f"{objects_json}"
        )
        
        try:
            output = await llm_client.generate_structured(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                response_model=ApplicabilityOutput
            )
            return output
        except Exception as e:
            logger.error(f"Applicability assessment failed: {str(e)}")
            raise

    async def run(self, document_id: str, semantic_objects: List[SemanticObject], data_dir: Path) -> ApplicabilityOutput:
        """
        Runs the applicability assessment and saves the result.
        """
        if not semantic_objects:
            # Return empty if nothing to assess
            return ApplicabilityOutput(
                overall_applicability_score=0.0,
                overall_reasoning="No semantic objects provided.",
                object_assessments=[]
            )
            
        output = await self.assess_applicability(semantic_objects)
        
        # Save output for debugging/pipeline flow
        pipeline_dir = data_dir / "pipeline_output" / document_id
        output_file = pipeline_dir / "applicability_assessment.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output.model_dump(), f, indent=2)
            
        return output

applicability_agent = ApplicabilityAgent()
