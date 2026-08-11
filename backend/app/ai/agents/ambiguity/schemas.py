from pydantic import BaseModel, Field
from typing import List, Optional

class ObjectAmbiguity(BaseModel):
    object_id: str = Field(description="The unique identifier of the semantic object")
    has_ambiguity: bool = Field(description="Whether this semantic object contains ambiguity")
    ambiguity_type: Optional[str] = Field(
        description="Category of ambiguity, e.g., 'unclear wording', 'undefined term', 'unclear scope', 'unclear deadline'", 
        default=None
    )
    explanation: str = Field(description="Explanation of the ambiguity or reasoning if not ambiguous")
    confidence_score: float = Field(description="Confidence score of this assessment between 0.0 and 1.0", ge=0.0, le=1.0)
    regulatory_context: Optional[str] = Field(description="Supporting context from the regulatory text", default=None)

class AmbiguityOutput(BaseModel):
    document_has_ambiguity: bool = Field(description="True if any semantic object in the document is ambiguous")
    overall_explanation: str = Field(description="Overall explanation of ambiguity across the document")
    object_assessments: List[ObjectAmbiguity] = Field(description="Detailed ambiguity assessment for each semantic object")
