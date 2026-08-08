from pydantic import BaseModel, Field
from typing import List, Optional

class ExtractedObligation(BaseModel):
    id: Optional[str] = Field(description="Unique UUID for this obligation", default=None)
    object_id: str = Field(description="The unique identifier of the source semantic object")
    title: str = Field(description="A concise, actionable title for the obligation")
    obligation_text: str = Field(description="The full normalized text of the obligation")
    category: str = Field(description="The category of the obligation, e.g., 'Reporting', 'Compliance', 'Security', 'Registration'")
    regulatory_reference: Optional[str] = Field(description="The clause or section reference", default=None)
    responsible_role: Optional[str] = Field(description="Responsible area or role, if inferable from text", default=None)
    deadline: Optional[str] = Field(description="Deadline or frequency, ONLY if explicitly stated", default=None)
    evidence_requirement: Optional[str] = Field(description="Required evidence or proof, ONLY if explicitly stated", default=None)
    confidence_score: float = Field(description="Confidence score between 0.0 and 1.0", ge=0.0, le=1.0)

class ObligationOutput(BaseModel):
    obligations: List[ExtractedObligation] = Field(description="List of normalized obligations extracted from the text")
