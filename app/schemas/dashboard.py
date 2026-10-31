from typing import List, Optional
import datetime
from pydantic import BaseModel

class DashboardStatsResponse(BaseModel):
    total_drivers: int
    compliant_drivers: int
    expiring_soon_drivers: int
    expired_drivers: int
    incomplete_drivers: int
    total_documents_uploaded: int
    missing_documents_count: int

class ExpiryAlertItem(BaseModel):
    driver_id: int
    driver_name: str
    driver_type: Optional[str] = "Driver"
    driver_callsign: Optional[str] = None
    field_key: str
    field_name: str
    date: Optional[datetime.date] = None
    days_remaining: Optional[int] = None
    status: str
    color: str
    label: str
    is_required: bool

class MissingDocumentItem(BaseModel):
    driver_id: int
    driver_name: str
    driver_type: Optional[str] = "Driver"
    driver_callsign: Optional[str] = None
    document_type_id: int
    document_name: str
    code: str

class DashboardOverviewResponse(BaseModel):
    stats: DashboardStatsResponse
    expiries: List[ExpiryAlertItem]
    missing_documents: List[MissingDocumentItem]
