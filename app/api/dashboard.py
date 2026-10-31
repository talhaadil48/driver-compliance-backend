from typing import List, Optional, Tuple
import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, selectinload
from app.api.deps import get_db, get_current_staff
from app.models.staff import StaffUser
from app.models.driver import Driver
from app.models.document_type import DocumentType
from app.models.document import DriverDocument
from app.schemas.dashboard import (
    DashboardStatsResponse, ExpiryAlertItem, MissingDocumentItem, DashboardOverviewResponse
)
from app.services.compliance import compute_driver_compliance
from app.services.cache import get_cached_doc_types

router = APIRouter(prefix="/dashboard", tags=["Compliance Dashboard"])

def _load_all_compliance_items(db: Session) -> Tuple[DashboardStatsResponse, List[ExpiryAlertItem], List[MissingDocumentItem]]:
    drivers = db.query(Driver).options(
        selectinload(Driver.documents)
    ).filter(Driver.is_active == True).all()

    all_doc_types = get_cached_doc_types(db)

    total_drivers = len(drivers)
    compliant_count = 0
    expiring_soon_count = 0
    expired_count = 0
    incomplete_count = 0
    missing_docs_total = 0

    alerts: List[ExpiryAlertItem] = []
    missing_list: List[MissingDocumentItem] = []
    total_uploaded = 0

    for d in drivers:
        total_uploaded += len(d.documents)
        comp = compute_driver_compliance(d, all_doc_types)
        status = comp["overall_status"]
        if status == "COMPLIANT":
            compliant_count += 1
        elif status == "EXPIRING_SOON":
            expiring_soon_count += 1
        elif status == "EXPIRED":
            expired_count += 1
        elif status == "INCOMPLETE":
            incomplete_count += 1

        missing_docs_total += len(comp["missing_required_docs"])

        for f in comp["fields_evaluation"]:
            f_status = f["status"]
            if f_status not in ["EXPIRED", "EXPIRING_SOON", "MISSING"]:
                continue
            if not f["is_required"] and f["date"] is None:
                continue

            alerts.append(ExpiryAlertItem(
                driver_id=d.id,
                driver_name=d.full_name,
                driver_type=d.type,
                driver_callsign=d.callsign,
                field_key=f["key"],
                field_name=f["name"],
                date=datetime.date.fromisoformat(f["date"]) if f["date"] else None,
                days_remaining=f["days_remaining"],
                status=f["status"],
                color=f["color"],
                label=f["label"],
                is_required=f["is_required"]
            ))

        for m in comp["missing_required_docs"]:
            missing_list.append(MissingDocumentItem(
                driver_id=d.id,
                driver_name=d.full_name,
                driver_type=d.type,
                driver_callsign=d.callsign,
                document_type_id=m["document_type_id"],
                document_name=m["document_name"],
                code=m["code"]
            ))

    def sort_key(item: ExpiryAlertItem):
        if item.status == "EXPIRED":
            return (0, item.days_remaining or 0)
        elif item.status == "EXPIRING_SOON":
            return (1, item.days_remaining or 0)
        elif item.status == "MISSING":
            return (2, 0)
        return (3, item.days_remaining or 9999)

    alerts.sort(key=sort_key)

    stats = DashboardStatsResponse(
        total_drivers=total_drivers,
        compliant_drivers=compliant_count,
        expiring_soon_drivers=expiring_soon_count,
        expired_drivers=expired_count,
        incomplete_drivers=incomplete_count,
        total_documents_uploaded=total_uploaded,
        missing_documents_count=missing_docs_total
    )

    return stats, alerts, missing_list

@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    stats, alerts, missing = _load_all_compliance_items(db)
    return DashboardOverviewResponse(
        stats=stats,
        expiries=alerts,
        missing_documents=missing
    )

@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    stats, _, _ = _load_all_compliance_items(db)
    return stats

@router.get("/expiries", response_model=List[ExpiryAlertItem])
def get_expiry_alerts(
    filter_type: Optional[str] = Query(None, description="EXPIRED, EXPIRING_SOON, MISSING, ALL"),
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    _, alerts, _ = _load_all_compliance_items(db)
    if filter_type and filter_type != "ALL":
        alerts = [a for a in alerts if a.status == filter_type]
    return alerts

@router.get("/missing-documents", response_model=List[MissingDocumentItem])
def get_missing_documents(
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    _, _, missing = _load_all_compliance_items(db)
    return missing
