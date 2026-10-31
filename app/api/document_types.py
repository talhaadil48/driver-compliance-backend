from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_staff
from app.models.staff import StaffUser
from app.models.document_type import DocumentType
from app.schemas.document_type import DocumentTypeResponse
from app.services.cache import get_cached_doc_types

router = APIRouter(prefix="/document-types", tags=["Document Types"])

@router.get("", response_model=List[DocumentTypeResponse])
def list_document_types(
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    return get_cached_doc_types(db)

@router.get("/{doc_type_id}", response_model=DocumentTypeResponse)
def get_document_type(
    doc_type_id: int,
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    dt = db.query(DocumentType).filter(DocumentType.id == doc_type_id).first()
    if not dt:
        raise HTTPException(status_code=404, detail="Document type not found")
    return dt
