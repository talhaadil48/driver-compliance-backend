from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class DriverAuditLogResponse(BaseModel):
    id: int
    driver_id: int
    staff_id: Optional[int] = None
    staff_name: str
    action_type: str # FIELD_UPDATE, DOCUMENT_UPLOAD, DOCUMENT_REPLACE, DOCUMENT_DELETE, DRIVER_CREATED
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
