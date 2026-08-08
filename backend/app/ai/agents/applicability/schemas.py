from pydantic import BaseModel, Field
from typing import List, Optional

class ObjectApplicability(BaseModel):
    object_id: str = Field(description="The unique identifier of the semantic object")
    is_applicable: bool = Field(description="Whether this semantic object is applicable to the target organization")
    reasoning: str = Field(description="The reasoning behind the applicability decision")
    confidence_score: float = Field(description="Confidence score between 0.0 and 1.0", ge=0.0, le=1.0)
    relevant_context: Optional[str] = Field(description="Any specific regulatory context that triggered this applicability", default=None)

class ApplicabilityOutput(BaseModel):
    overall_applicability_score: float = Field(description="Overall applicability score for the entire document, from 0.0 to 1.0", ge=0.0, le=1.0)
    overall_reasoning: str = Field(description="Overall reasoning for the document's applicability to the target organization")
    object_assessments: List[ObjectApplicability] = Field(description="Detailed applicability assessment for each semantic object")
