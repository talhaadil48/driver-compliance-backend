from typing import List, Optional
from pydantic import BaseModel

class CouncilRequirementBase(BaseModel):
    council_code: str
    council_name: str
    description: Optional[str] = None
    required_expiry_fields: List[str]
    required_document_codes: List[str]

class CouncilRequirementUpdate(BaseModel):
    required_expiry_fields: List[str]
    required_document_codes: List[str]
    description: Optional[str] = None

class CouncilRequirementResponse(CouncilRequirementBase):
    id: int

    class Config:
        from_attributes = True

class CouncilComplianceCheckResponse(BaseModel):
    driver_id: int
    driver_name: str
    council_code: str
    is_compliant: bool
    missing_expiry_fields: List[str]
    expired_fields: List[str]
    missing_documents: List[str]
