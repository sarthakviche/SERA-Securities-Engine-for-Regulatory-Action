from pydantic import BaseModel, Field
from typing import List, Optional

class GeneratedTask(BaseModel):
    source_obligation_id: str = Field(description="The unique identifier of the source obligation")
    title: str = Field(description="A concise, actionable title for the task")
    description: str = Field(description="A detailed description of the operational task to be performed")
    priority: str = Field(description="Priority of the task: 'High', 'Medium', or 'Low'")
    owner_role: Optional[str] = Field(description="Responsible owner or role, ONLY if inferable from the obligation", default=None)
    deadline: Optional[str] = Field(description="Deadline for the task, ONLY if derived from the obligation", default=None)
    required_evidence: Optional[str] = Field(description="Required evidence to prove completion", default=None)

class TaskGenerationOutput(BaseModel):
    tasks: List[GeneratedTask] = Field(description="List of operational tasks generated from obligations")
