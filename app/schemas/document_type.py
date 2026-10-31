from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class DocumentTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    requires_expiry: bool = False
    requires_issue_date: bool = False
    is_mandatory: bool = False

class DocumentTypeCreate(DocumentTypeBase):
    pass

class DocumentTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    requires_expiry: Optional[bool] = None
    requires_issue_date: Optional[bool] = None
    is_mandatory: Optional[bool] = None

class DocumentTypeResponse(DocumentTypeBase):
    id: int
    code: str
    is_custom: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
