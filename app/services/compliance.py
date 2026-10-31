from datetime import date, datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from app.models.driver import Driver
from app.models.document import DriverDocument
from app.models.document_type import DocumentType
from app.models.driver_custom_field import DriverCustomField

# Status Constants
STATUS_RED_EXPIRED = "EXPIRED" # RED
STATUS_RED_MISSING = "MISSING" # RED
STATUS_YELLOW_EXPIRING = "EXPIRING_SOON" # YELLOW (<= 30 days)
STATUS_GREEN_VALID = "VALID" # GREEN (> 30 days)
STATUS_GREY_NOT_APPLICABLE = "NOT_APPLICABLE" # GREY

def evaluate_date_status(target_date: Optional[date], is_required: bool = True) -> Dict[str, Any]:
    today = date.today()

    if target_date is None:
        if is_required:
            return {
                "status": STATUS_RED_MISSING,
                "color": "red",
                "label": "Missing (Required)",
                "days_remaining": None,
                "is_urgent": True
            }
        else:
            return {
                "status": STATUS_GREY_NOT_APPLICABLE,
                "color": "gray",
                "label": "Not Set (Optional)",
                "days_remaining": None,
                "is_urgent": False
            }

    diff_days = (target_date - today).days

    if diff_days < 0:
        return {
            "status": STATUS_RED_EXPIRED,
            "color": "red",
            "label": f"Expired ({abs(diff_days)} days ago)",
            "days_remaining": diff_days,
            "is_urgent": True
        }
    elif diff_days <= 30:
        return {
            "status": STATUS_YELLOW_EXPIRING,
            "color": "yellow",
            "label": f"Expiring Soon ({diff_days} days left)",
            "days_remaining": diff_days,
            "is_urgent": True
        }
    else:
        return {
            "status": STATUS_GREEN_VALID,
            "color": "green",
            "label": f"Valid ({diff_days} days left)",
            "days_remaining": diff_days,
            "is_urgent": False
        }

def compute_driver_compliance(
    driver: Driver,
    all_doc_types: List[DocumentType]
) -> Dict[str, Any]:
    today = date.today()
    fields_eval = []
    
    # Standard Expiry Fields
    standard_fields = [
        {
            "key": "dbs_update_service_expiry",
            "name": "DBS Update Service Expiry",
            "date": driver.dbs_update_service_expiry,
            "is_required": True
        },
        {
            "key": "safeguarding_expiry",
            "name": "Safeguarding Expiry",
            "date": driver.safeguarding_expiry,
            "is_required": True
        },
        {
            "key": "first_aid_expiry",
            "name": "First Aid Expiry",
            "date": driver.first_aid_expiry,
            "is_required": True
        },
        {
            "key": "autism_awareness_expiry",
            "name": "Autism Awareness Expiry",
            "date": driver.autism_awareness_expiry,
            "is_required": True
        }
    ]

    for sf in standard_fields:
        res = evaluate_date_status(sf["date"], sf["is_required"])
        fields_eval.append({
            "key": sf["key"],
            "name": sf["name"],
            "date": sf["date"].isoformat() if sf["date"] else None,
            "is_required": sf["is_required"],
            "is_custom": False,
            **res
        })

    # Evaluate Documents
    uploaded_doc_type_ids = {doc.document_type_id for doc in driver.documents}
    docs_summary = []
    missing_required_docs = []

    for dt in all_doc_types:
        is_uploaded = dt.id in uploaded_doc_type_ids
        is_doc_required = dt.is_mandatory

        if is_doc_required and not is_uploaded:
            missing_required_docs.append({
                "document_type_id": dt.id,
                "document_name": dt.name,
                "code": dt.code
            })

        docs_summary.append({
            "document_type_id": dt.id,
            "code": dt.code,
            "name": dt.name,
            "is_mandatory": dt.is_mandatory,
            "is_uploaded": is_uploaded,
            "files": [
                {
                    "id": d.id,
                    "file_name": d.file_name,
                    "file_size": d.file_size,
                    "mime_type": d.mime_type,
                    "page_number": d.page_number,
                    "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None
                }
                for d in driver.documents if d.document_type_id == dt.id
            ]
        })

    # Overall Status
    has_expired = any(f["status"] == STATUS_RED_EXPIRED for f in fields_eval if f["is_required"])
    has_missing_field = any(f["status"] == STATUS_RED_MISSING for f in fields_eval if f["is_required"])
    has_expiring_soon = any(f["status"] == STATUS_YELLOW_EXPIRING for f in fields_eval if f["is_required"])
    has_missing_doc = len(missing_required_docs) > 0

    if has_expired:
        overall_status = "EXPIRED"
        overall_color = "red"
        overall_badge = "Action Required (Expired)"
    elif has_missing_field or has_missing_doc:
        overall_status = "INCOMPLETE"
        overall_color = "red"
        overall_badge = "Incomplete / Missing Requirements"
    elif has_expiring_soon:
        overall_status = "EXPIRING_SOON"
        overall_color = "yellow"
        overall_badge = "Expiring Soon (< 30 days)"
    else:
        overall_status = "COMPLIANT"
        overall_color = "green"
        overall_badge = "Fully Compliant"

    return {
        "overall_status": overall_status,
        "overall_color": overall_color,
        "overall_badge": overall_badge,
        "has_expired": has_expired,
        "has_missing_field": has_missing_field,
        "has_missing_doc": has_missing_doc,
        "has_expiring_soon": has_expiring_soon,
        "fields_evaluation": fields_eval,
        "missing_required_docs": missing_required_docs,
        "documents_summary": docs_summary
    }
