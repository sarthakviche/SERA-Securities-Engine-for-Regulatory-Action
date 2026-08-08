import json
import logging
from typing import List, Dict, Any
from pathlib import Path

from app.ai.llm_client import llm_client
from app.ai.agents.obligation.schemas import ObligationOutput, ExtractedObligation
from app.ai.agents.task_generation.schemas import TaskGenerationOutput, GeneratedTask
from .prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class TaskGenerationAgent:
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT

    async def generate_tasks(self, obligations: ObligationOutput) -> TaskGenerationOutput:
        if not obligations.obligations:
            return TaskGenerationOutput(tasks=[])
            
        payload = {
            "obligations": [ob.model_dump() for ob in obligations.obligations]
        }
        
        user_prompt = (
            "Generate operational tasks for the following regulatory obligations:\n\n"
            f"{json.dumps(payload, indent=2)}"
        )
        
        try:
            output = await llm_client.generate_structured(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                response_model=TaskGenerationOutput
            )
            return output
        except Exception as e:
            logger.error(f"Task generation failed: {str(e)}")
            raise

    async def run(self, document_id: str, obligations: ObligationOutput, data_dir: Path) -> TaskGenerationOutput:
        """
        Runs the task generation and saves the result.
        """
        output = await self.generate_tasks(obligations)
        
        # Save output for debugging/pipeline flow
        pipeline_dir = data_dir / "pipeline_output" / document_id
        output_file = pipeline_dir / "tasks.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output.model_dump(), f, indent=2)
            
        return output

task_generation_agent = TaskGenerationAgent()
