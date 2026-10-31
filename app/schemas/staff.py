from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

class StaffLoginRequest(BaseModel):
    email: EmailStr
    password: str

class StaffTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    staff: "StaffResponse"

class StaffCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "staff" # admin, staff, viewer

class StaffUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class StaffResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

StaffTokenResponse.model_rebuild()
