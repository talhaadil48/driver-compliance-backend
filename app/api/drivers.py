from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_
from app.api.deps import get_db, get_current_staff
from app.models.staff import StaffUser
from app.models.driver import Driver
from app.models.document_type import DocumentType
from app.models.document import DriverDocument
from app.models.audit_log import DriverAuditLog
from app.schemas.driver import (
    DriverCreate, DriverUpdate, DriverListResponse, DriverDetailResponse
)
from app.schemas.audit_log import DriverAuditLogResponse
from app.services.compliance import compute_driver_compliance
from app.services.cache import get_cached_doc_types
from app.services.audit import record_driver_audit, FIELD_LABELS

router = APIRouter(prefix="/drivers", tags=["Drivers Management"])

@router.get("", response_model=List[DriverListResponse])
def list_drivers(
    q: Optional[str] = Query(None, description="Search by name, phone, NI number, or DBS number"),
    status_filter: Optional[str] = Query(None, description="Filter: COMPLIANT, EXPIRING_SOON, EXPIRED, INCOMPLETE"),
    type_filter: Optional[str] = Query(None, description="Filter: Driver, Passenger"),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    query = db.query(Driver).options(
        selectinload(Driver.documents)
    )
    if active_only:
        query = query.filter(Driver.is_active == True)

    if type_filter and type_filter != "ALL":
        query = query.filter(Driver.type == type_filter)

    if q:
        search = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Driver.full_name.ilike(search),
                Driver.callsign.ilike(search),
                Driver.type.ilike(search),
                Driver.phone.ilike(search),
                Driver.national_insurance_number.ilike(search),
                Driver.dbs_certificate_number.ilike(search),
                Driver.dbs_update_service_reference.ilike(search)
            )
        )

    drivers = query.order_by(Driver.full_name.asc()).all()
    all_doc_types = get_cached_doc_types(db)

    result = []
    for d in drivers:
        comp = compute_driver_compliance(d, all_doc_types)

        if status_filter and comp["overall_status"] != status_filter:
            continue

        result.append(
            DriverListResponse(
                id=d.id,
                full_name=d.full_name,
                type=d.type,
                callsign=d.callsign,
                phone=d.phone,
                dob=d.dob,
                national_insurance_number=d.national_insurance_number,
                is_active=d.is_active,
                created_at=d.created_at,
                overall_status=comp["overall_status"],
                overall_color=comp["overall_color"],
                overall_badge=comp["overall_badge"],
                has_expired=comp["has_expired"],
                has_missing_field=comp["has_missing_field"],
                has_missing_doc=comp["has_missing_doc"],
                has_expiring_soon=comp["has_expiring_soon"],
                documents_count=len(d.documents)
            )
        )

    return result

@router.post("", response_model=DriverDetailResponse)
def create_driver(
    data: DriverCreate,
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    driver = Driver(
        full_name=data.full_name.strip(),
        type=data.type or "Driver",
        callsign=data.callsign.strip() if data.callsign else None,
        dob=data.dob,
        national_insurance_number=data.national_insurance_number.strip() if data.national_insurance_number else None,
        dbs_certificate_number=data.dbs_certificate_number.strip() if data.dbs_certificate_number else None,
        dbs_update_service_reference=data.dbs_update_service_reference.strip() if data.dbs_update_service_reference else None,
        email=data.email.strip() if data.email else None,
        phone=data.phone.strip() if data.phone else None,
        address=data.address.strip() if data.address else None,
        notes=data.notes.strip() if data.notes else None,
        is_active=data.is_active,
        dbs_update_service_expiry=data.dbs_update_service_expiry,
        safeguarding_expiry=data.safeguarding_expiry,
        first_aid_expiry=data.first_aid_expiry,
        autism_awareness_expiry=data.autism_awareness_expiry,
        autism_awareness_expiry_enabled=data.autism_awareness_expiry_enabled,
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)

    # Record audit log for driver creation
    record_driver_audit(
        db=db,
        driver_id=driver.id,
        staff=current_staff,
        action_type="DRIVER_CREATED",
        field_name="Personnel Profile",
        old_value=None,
        new_value=f"{driver.full_name} ({driver.type or 'Driver'})",
        notes="Profile created"
    )
    db.commit()

    all_doc_types = get_cached_doc_types(db)
    comp = compute_driver_compliance(driver, all_doc_types)

    resp = DriverDetailResponse.model_validate(driver)
    resp.compliance = comp
    return resp

@router.get("/{driver_id}", response_model=DriverDetailResponse)
def get_driver_detail(
    driver_id: int,
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    driver = db.query(Driver).options(
        selectinload(Driver.documents)
    ).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver record not found")

    all_doc_types = get_cached_doc_types(db)
    comp = compute_driver_compliance(driver, all_doc_types)

    resp = DriverDetailResponse.model_validate(driver)
    resp.compliance = comp
    return resp

@router.put("/{driver_id}", response_model=DriverDetailResponse)
def update_driver_fields(
    driver_id: int,
    data: DriverUpdate,
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    driver = db.query(Driver).options(
        selectinload(Driver.documents)
    ).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver record not found")

    update_dict = data.model_dump(exclude_unset=True)
    
    # Audit log changes
    for field, val in update_dict.items():
        old_val = getattr(driver, field, None)
        
        # Compare normalized values
        str_old = "" if old_val is None else str(old_val).strip()
        str_new = "" if val is None else str(val).strip()
        
        if str_old != str_new:
            field_label = FIELD_LABELS.get(field, field.replace('_', ' ').title())
            record_driver_audit(
                db=db,
                driver_id=driver.id,
                staff=current_staff,
                action_type="FIELD_UPDATE",
                field_name=field_label,
                old_value=old_val,
                new_value=val
            )
            setattr(driver, field, val)

    db.commit()
    db.refresh(driver)

    all_doc_types = get_cached_doc_types(db)
    comp = compute_driver_compliance(driver, all_doc_types)

    resp = DriverDetailResponse.model_validate(driver)
    resp.compliance = comp
    return resp

@router.get("/{driver_id}/audit-logs", response_model=List[DriverAuditLogResponse])
def get_driver_audit_logs(
    driver_id: int,
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """Retrieve full change history and audit trail for a specific driver."""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver record not found")

    logs = db.query(DriverAuditLog).filter(
        DriverAuditLog.driver_id == driver_id
    ).order_by(DriverAuditLog.created_at.desc()).all()

    return logs

@router.delete("/{driver_id}")
def delete_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver record not found")

    db.delete(driver)
    db.commit()
    return {"success": True, "message": "Driver record removed successfully"}
