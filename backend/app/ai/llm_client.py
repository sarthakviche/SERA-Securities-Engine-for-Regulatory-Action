import json
import logging
from typing import Any, Type, TypeVar
import httpx
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class LLMClientError(Exception):
    pass

class LLMClient:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.LLM_MODEL or "llama-3.3-70b-versatile"
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    async def generate_structured(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> T:
        """
        Calls the LLM and forces the output to match the Pydantic schema using JSON mode
        and schema prompting.
        """
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set in environment variables")
            
        schema = response_model.model_json_schema()
        
        # Enforce JSON mode and provide the schema in the system prompt
        full_system_prompt = (
            f"{system_prompt}\n\n"
            "You MUST output valid JSON only. Do not include markdown formatting like ```json.\n"
            "Your output must strictly adhere to the following JSON schema:\n"
            f"{json.dumps(schema, indent=2)}"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(self.base_url, headers=headers, json=payload)
                    response.raise_for_status()
                    
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    
                    # Strip markdown blocks if the LLM leaked them despite instructions
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.endswith("```"):
                        content = content[:-3]
                    
                    parsed_json = json.loads(content)
                    return response_model.model_validate(parsed_json)
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    logger.warning(f"Rate limited. Retrying in 35 seconds... (Attempt {attempt+1}/{max_retries})")
                    import asyncio
                    await asyncio.sleep(35)
                    continue
                logger.error(f"LLM API Error: {e.response.text}")
                raise LLMClientError(f"LLM API request failed with status {e.response.status_code}") from e
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM output as JSON: {content}")
                raise LLMClientError("LLM returned invalid JSON") from e
            except Exception as e:
                logger.error(f"LLM Client error: {str(e)}")
                raise LLMClientError(f"LLM invocation failed: {str(e)}") from e

llm_client = LLMClient()
