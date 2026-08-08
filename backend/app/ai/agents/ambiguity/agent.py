import json
import logging
from typing import List, Dict, Any
from pathlib import Path

from app.ai.llm_client import llm_client
from app.ai.agents.extraction.schemas import SemanticObject
from app.ai.agents.applicability.schemas import ApplicabilityOutput
from app.ai.agents.ambiguity.schemas import AmbiguityOutput, ObjectAmbiguity

logger = logging.getLogger(__name__)

class AmbiguityAgent:
    def __init__(self):
        self.system_prompt = (
            "You are a regulatory compliance expert analyzing regulatory text for ambiguity. "
            "Your task is to review the provided semantic objects and their applicability assessment, "
            "and identify any ambiguities. Consider issues such as unclear wording, undefined terms, "
            "unclear scope, conflicting interpretations, unclear responsibility, or unclear deadlines. "
            "If there is no ambiguity, explicitly state that it is clear and explain why. "
            "Base your assessment strictly on the provided regulatory text and context. Do not invent information."
        )

    async def detect_ambiguity(self, semantic_objects: List[SemanticObject], applicability: ApplicabilityOutput) -> AmbiguityOutput:
        # We focus primarily on objects that were deemed applicable, but we pass all to maintain context
        payload = {
            "semantic_objects": [obj.model_dump() for obj in semantic_objects],
            "applicability_assessment": applicability.model_dump()
        }
        
        user_prompt = (
            "Analyze the following semantic objects and their applicability assessment for any regulatory ambiguity:\n\n"
            f"{json.dumps(payload, indent=2)}"
        )
        
        try:
            output = await llm_client.generate_structured(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                response_model=AmbiguityOutput
            )
            return output
        except Exception as e:
            logger.error(f"Ambiguity detection failed: {str(e)}")
            raise

    async def run(self, document_id: str, semantic_objects: List[SemanticObject], applicability: ApplicabilityOutput, data_dir: Path) -> AmbiguityOutput:
        """
        Runs the ambiguity detection and saves the result.
        """
        if not semantic_objects:
            return AmbiguityOutput(
                document_has_ambiguity=False,
                overall_explanation="No semantic objects provided.",
                object_assessments=[]
            )
            
        output = await self.detect_ambiguity(semantic_objects, applicability)
        
        # Save output for debugging/pipeline flow
        pipeline_dir = data_dir / "pipeline_output" / document_id
        output_file = pipeline_dir / "ambiguity_assessment.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output.model_dump(), f, indent=2)
            
        return output

ambiguity_agent = AmbiguityAgent()
