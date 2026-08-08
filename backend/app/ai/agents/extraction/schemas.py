from pydantic import BaseModel, Field
from typing import List, Optional

class SemanticObject(BaseModel):
    object_id: str = Field(description="A unique identifier for this semantic object (e.g. obj_1)")
    clause_id: Optional[str] = Field(description="The clause_id from which this was extracted, if applicable", default=None)
    type: str = Field(description="The type of the object (e.g., 'obligation', 'definition', 'date', 'exemption')")
    text: Optional[str] = Field(description="The raw or slightly normalized text representing the object", default=None)
    context: Optional[str] = Field(description="Brief context about where this applies", default=None)

class ExtractionOutput(BaseModel):
    objects: List[SemanticObject] = Field(description="List of extracted semantic objects")
