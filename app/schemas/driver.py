from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel

class DriverBase(BaseModel):
    full_name: str
    type: Optional[str] = "Driver"
    callsign: Optional[str] = None
    dob: Optional[date] = None
    national_insurance_number: Optional[str] = None
    dbs_certificate_number: Optional[str] = None
    dbs_update_service_reference: Optional[str] = None
    
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True

    # Expiry Dates
    dbs_update_service_expiry: Optional[date] = None
    safeguarding_expiry: Optional[date] = None
    first_aid_expiry: Optional[date] = None
    autism_awareness_expiry: Optional[date] = None
    autism_awareness_expiry_enabled: bool = False

class DriverCreate(DriverBase):
    pass

class DriverUpdate(BaseModel):
    full_name: Optional[str] = None
    type: Optional[str] = None
    callsign: Optional[str] = None
    dob: Optional[date] = None
    national_insurance_number: Optional[str] = None
    dbs_certificate_number: Optional[str] = None
    dbs_update_service_reference: Optional[str] = None
    
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

    # Expiry Dates
    dbs_update_service_expiry: Optional[date] = None
    safeguarding_expiry: Optional[date] = None
    first_aid_expiry: Optional[date] = None
    autism_awareness_expiry: Optional[date] = None
    autism_awareness_expiry_enabled: Optional[bool] = None

class DriverListResponse(BaseModel):
    id: int
    full_name: str
    type: Optional[str] = "Driver"
    callsign: Optional[str] = None
    phone: Optional[str] = None
    dob: Optional[date] = None
    national_insurance_number: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    
    # Compliance Summary
    overall_status: str
    overall_color: str
    overall_badge: str
    has_expired: bool
    has_missing_field: bool
    has_missing_doc: bool
    has_expiring_soon: bool
    documents_count: int

    class Config:
        from_attributes = True

class DriverDetailResponse(DriverBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    compliance: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
