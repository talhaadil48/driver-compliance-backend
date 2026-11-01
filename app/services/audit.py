from datetime import date, datetime
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models.audit_log import DriverAuditLog
from app.models.staff import StaffUser

FIELD_LABELS = {
    "full_name": "Full Name",
    "type": "Profile Type",
    "callsign": "Callsign / Badge ID",
    "dob": "Date of Birth",
    "national_insurance_number": "National Insurance Number",
    "dbs_certificate_number": "DBS Certificate Number",
    "dbs_update_service_reference": "DBS Update Service Ref",
    "email": "Email Address",
    "phone": "Phone Number",
    "address": "Residential Address",
    "notes": "Internal Notes",
    "is_active": "Active Status",
    "council_affiliation": "Council Affiliation",
    "dbs_update_service_expiry": "DBS Update Service Expiry",
    "safeguarding_expiry": "Safeguarding Certificate Expiry",
    "first_aid_expiry": "First Aid Certificate Expiry",
    "autism_awareness_expiry": "Autism Awareness Expiry",
    "autism_awareness_expiry_enabled": "Autism Awareness Tracking Enabled",
    "driving_licence_expiry": "Driving Licence Expiry",
    "passport_expiry": "Passport Expiry",
    "driver_id_badge_expiry": "Driver ID Badge Expiry",
}

def format_val(val: Any) -> Optional[str]:
    if val is None or val == "":
        return None
    if isinstance(val, (date, datetime)):
        # Format as UK DD/MM/YYYY
        return val.strftime("%d/%m/%Y")
    if isinstance(val, bool):
        return "Yes" if val else "No"
    return str(val).strip()

def record_driver_audit(
    db: Session,
    driver_id: int,
    staff: Optional[StaffUser],
    action_type: str,
    field_name: str,
    old_value: Any,
    new_value: Any,
    notes: Optional[str] = None
) -> DriverAuditLog:
    """Records an audit log entry for any driver field change or document change."""
    staff_id = staff.id if staff else None
    staff_name = staff.full_name if staff and staff.full_name else (staff.email if staff else "System")

    fmt_old = format_val(old_value)
    fmt_new = format_val(new_value)

    log_entry = DriverAuditLog(
        driver_id=driver_id,
        staff_id=staff_id,
        staff_name=staff_name,
        action_type=action_type,
        field_name=field_name,
        old_value=fmt_old,
        new_value=fmt_new,
        notes=notes.strip() if notes else None
    )
    db.add(log_entry)
    return log_entry
