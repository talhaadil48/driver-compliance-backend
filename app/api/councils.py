import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_staff
from app.models.staff import StaffUser
from app.models.driver import Driver
from app.models.document_type import DocumentType
from app.models.council import CouncilRequirement
from app.schemas.council import CouncilRequirementResponse, CouncilRequirementUpdate

router = APIRouter(prefix="/councils", tags=["Council Requirements"])

@router.get("/requirements", response_model=List[CouncilRequirementResponse])
def get_council_requirements(
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    councils = db.query(CouncilRequirement).order_by(CouncilRequirement.council_code.asc()).all()
    results = []
    for c in councils:
        try:
            exp_fields = json.loads(c.required_expiry_fields)
        except Exception:
            exp_fields = []
        try:
            doc_codes = json.loads(c.required_document_codes)
        except Exception:
            doc_codes = []

        results.append(CouncilRequirementResponse(
            id=c.id,
            council_code=c.council_code,
            council_name=c.council_name,
            description=c.description,
            required_expiry_fields=exp_fields,
            required_document_codes=doc_codes
        ))
    return results

@router.put("/requirements/{council_code}", response_model=CouncilRequirementResponse)
def update_council_requirements(
    council_code: str,
    data: CouncilRequirementUpdate,
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    c = db.query(CouncilRequirement).filter(
        CouncilRequirement.council_code == council_code.upper().strip()
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Council '{council_code}' not found")

    c.required_expiry_fields = json.dumps(data.required_expiry_fields)
    c.required_document_codes = json.dumps(data.required_document_codes)
    if data.description is not None:
        c.description = data.description

    db.commit()
    db.refresh(c)

    return CouncilRequirementResponse(
        id=c.id,
        council_code=c.council_code,
        council_name=c.council_name,
        description=c.description,
        required_expiry_fields=data.required_expiry_fields,
        required_document_codes=data.required_document_codes
    )

@router.get("/check/{driver_id}")
def check_driver_council_eligibility(
    driver_id: int,
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver record not found")

    councils = db.query(CouncilRequirement).all()
    all_doc_types = {dt.code: dt for dt in db.query(DocumentType).all()}
    uploaded_codes = {doc.document_type.code for doc in driver.documents if doc.document_type}

    report = {}
    for c in councils:
        try:
            exp_fields = json.loads(c.required_expiry_fields)
        except Exception:
            exp_fields = []
        try:
            doc_codes = json.loads(c.required_document_codes)
        except Exception:
            doc_codes = []

        missing_fields = []
        expired_fields = []
        for f in exp_fields:
            val = getattr(driver, f, None)
            from datetime import date
            if val is None:
                missing_fields.append(f)
            elif val < date.today():
                expired_fields.append(f)

        missing_docs = [code for code in doc_codes if code not in uploaded_codes]
        is_compliant = (len(missing_fields) == 0 and len(expired_fields) == 0 and len(missing_docs) == 0)

        report[c.council_code] = {
            "council_name": c.council_name,
            "is_compliant": is_compliant,
            "missing_fields": missing_fields,
            "expired_fields": expired_fields,
            "missing_documents": missing_docs
        }

    return {
        "driver_id": driver.id,
        "driver_name": driver.full_name,
        "council_affiliation": driver.council_affiliation,
        "councils": report
    }
