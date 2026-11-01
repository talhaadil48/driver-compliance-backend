import os
import re
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response, status
from fastapi.responses import StreamingResponse
import io
from sqlalchemy.orm import Session, joinedload
from app.api.deps import get_db, get_current_staff
from app.models.staff import StaffUser
from app.models.driver import Driver
from app.models.document_type import DocumentType
from app.models.document import DriverDocument
from app.schemas.document import (
    DocumentResponse,
    DocumentUploadResponse,
    PresignUploadRequest,
    PresignUploadResponse,
    ConfirmUploadRequest,
    PresignReplaceRequest,
    ConfirmReplaceRequest,
)
from app.services.storage import storage_service
from app.services.audit import record_driver_audit

router = APIRouter(prefix="/documents", tags=["Driver Documents"])

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png"
}

@router.get("/driver/{driver_id}", response_model=List[DocumentResponse])
def get_driver_documents(
    driver_id: int,
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    docs = db.query(DriverDocument).options(
        joinedload(DriverDocument.document_type),
        joinedload(DriverDocument.uploaded_by)
    ).filter(DriverDocument.driver_id == driver_id).all()
    results = []
    for d in docs:
        results.append(DocumentResponse(
            id=d.id,
            driver_id=d.driver_id,
            document_type_id=d.document_type_id,
            document_type_name=d.document_type.name if d.document_type else "Unknown",
            document_type_code=d.document_type.code if d.document_type else "unknown",
            file_name=d.file_name,
            file_size=d.file_size,
            mime_type=d.mime_type,
            page_number=d.page_number,
            notes=d.notes,
            storage_type=d.storage_type,
            uploaded_at=d.uploaded_at,
            uploaded_by_name=d.uploaded_by.full_name if d.uploaded_by else None
        ))
    return results

@router.post("/driver/{driver_id}/presign-upload", response_model=PresignUploadResponse)
def presign_upload_document(
    driver_id: int,
    data: PresignUploadRequest,
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """Generates direct presigned S3 upload URL for frontend (bypasses serverless file limits)."""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver record not found")

    doc_type = db.query(DocumentType).filter(DocumentType.id == data.document_type_id).first()
    if not doc_type:
        raise HTTPException(status_code=404, detail="Document type not found")

    clean_driver_name = re.sub(r'[^a-zA-Z0-9_\-]', '', driver.full_name.strip().replace(' ', '_'))
    driver_folder = f"{driver.id}_{clean_driver_name}" if clean_driver_name else str(driver.id)

    raw_name = os.path.basename(data.file_name or "uploaded_file")
    clean_file_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', raw_name)
    file_key = f"{storage_service.project_folder}/{driver_folder}/{clean_file_name}"

    upload_url = storage_service.generate_presigned_upload_url(
        file_key=file_key,
        content_type=data.mime_type
    )
    if not upload_url:
        raise HTTPException(status_code=500, detail="Could not generate presigned upload URL")

    return PresignUploadResponse(
        upload_url=upload_url,
        file_key=file_key,
        file_name=raw_name,
        storage_type="s3"
    )

@router.post("/driver/{driver_id}/confirm-upload", response_model=DocumentUploadResponse)
def confirm_upload_document(
    driver_id: int,
    data: ConfirmUploadRequest,
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """Confirms document record in database after direct S3 frontend upload."""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver record not found")

    doc_type = db.query(DocumentType).filter(DocumentType.id == data.document_type_id).first()
    if not doc_type:
        raise HTTPException(status_code=404, detail="Document type not found")

    doc = DriverDocument(
        driver_id=driver_id,
        document_type_id=data.document_type_id,
        file_name=data.file_name,
        file_key=data.file_key,
        file_size=data.file_size,
        mime_type=data.mime_type,
        storage_type=data.storage_type,
        page_number=1,
        notes=data.notes.strip() if data.notes else None,
        uploaded_by_staff_id=current_staff.id
    )
    db.add(doc)
    
    # Audit log
    record_driver_audit(
        db=db,
        driver_id=driver_id,
        staff=current_staff,
        action_type="DOCUMENT_UPLOAD",
        field_name=f"Document: {doc_type.name}",
        old_value=None,
        new_value=f"{data.file_name} (Uploaded)",
        notes=data.notes
    )
    db.commit()
    db.refresh(doc)

    return DocumentUploadResponse(
        success=True,
        message=f"{doc_type.name} uploaded successfully",
        document=DocumentResponse(
            id=doc.id,
            driver_id=doc.driver_id,
            document_type_id=doc.document_type_id,
            document_type_name=doc_type.name,
            document_type_code=doc_type.code,
            file_name=doc.file_name,
            file_size=doc.file_size,
            mime_type=doc.mime_type,
            page_number=doc.page_number,
            notes=doc.notes,
            storage_type=doc.storage_type,
            uploaded_at=doc.uploaded_at,
            uploaded_by_name=current_staff.full_name
        )
    )

@router.post("/{document_id}/presign-replace", response_model=PresignUploadResponse)
def presign_replace_document(
    document_id: int,
    data: PresignReplaceRequest,
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """Generates direct presigned S3 replacement URL and deletes old S3 file."""
    doc = db.query(DriverDocument).filter(DriverDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document record not found")

    # Delete old file from S3
    try:
        storage_service.delete_file(doc.file_key, doc.storage_type)
    except Exception:
        pass

    driver = db.query(Driver).filter(Driver.id == doc.driver_id).first()
    clean_driver_name = re.sub(r'[^a-zA-Z0-9_\-]', '', driver.full_name.strip().replace(' ', '_')) if driver else ""
    driver_folder = f"{doc.driver_id}_{clean_driver_name}" if clean_driver_name else str(doc.driver_id)

    raw_name = os.path.basename(data.file_name or "replaced_file")
    clean_file_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', raw_name)
    file_key = f"{storage_service.project_folder}/{driver_folder}/{clean_file_name}"

    upload_url = storage_service.generate_presigned_upload_url(
        file_key=file_key,
        content_type=data.mime_type
    )
    if not upload_url:
        raise HTTPException(status_code=500, detail="Could not generate presigned upload URL")

    return PresignUploadResponse(
        upload_url=upload_url,
        file_key=file_key,
        file_name=raw_name,
        storage_type="s3"
    )

@router.post("/{document_id}/confirm-replace", response_model=DocumentUploadResponse)
def confirm_replace_document(
    document_id: int,
    data: ConfirmReplaceRequest,
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """Confirms document replacement in database after direct S3 upload."""
    doc = db.query(DriverDocument).filter(DriverDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document record not found")

    old_file_name = doc.file_name
    doc_type_name = doc.document_type.name if doc.document_type else "Document"

    doc.file_name = data.file_name
    doc.file_key = data.file_key
    doc.file_size = data.file_size
    doc.mime_type = data.mime_type
    doc.storage_type = data.storage_type
    if data.notes is not None:
        doc.notes = data.notes.strip()
    doc.uploaded_by_staff_id = current_staff.id

    # Audit log
    record_driver_audit(
        db=db,
        driver_id=doc.driver_id,
        staff=current_staff,
        action_type="DOCUMENT_REPLACE",
        field_name=f"Document: {doc_type_name}",
        old_value=f"Old file: {old_file_name}",
        new_value=f"Replaced with: {data.file_name}",
        notes=data.notes
    )

    db.commit()
    db.refresh(doc)

    return DocumentUploadResponse(
        success=True,
        message="Document replaced successfully",
        document=DocumentResponse(
            id=doc.id,
            driver_id=doc.driver_id,
            document_type_id=doc.document_type_id,
            document_type_name=doc.document_type.name if doc.document_type else "",
            document_type_code=doc.document_type.code if doc.document_type else "",
            file_name=doc.file_name,
            file_size=doc.file_size,
            mime_type=doc.mime_type,
            page_number=doc.page_number,
            notes=doc.notes,
            storage_type=doc.storage_type,
            uploaded_at=doc.uploaded_at,
            uploaded_by_name=current_staff.full_name
        )
    )

@router.post("/driver/{driver_id}/upload", response_model=DocumentUploadResponse)
async def upload_driver_document(
    driver_id: int,
    document_type_id: int = Form(...),
    page_number: int = Form(1),
    notes: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    # Verify driver
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver record not found")

    # Verify document type
    doc_type = db.query(DocumentType).filter(DocumentType.id == document_type_id).first()
    if not doc_type:
        raise HTTPException(status_code=404, detail="Document type not found")

    # Validate file mime type
    mime = file.content_type or "application/octet-stream"
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {mime}. Allowed types: PDF, JPG, JPEG, PNG"
        )

    content = await file.read()
    file_size = len(content)
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Clean driver folder: e.g. "5_Emre_Acun"
    clean_driver_name = re.sub(r'[^a-zA-Z0-9_\-]', '', driver.full_name.strip().replace(' ', '_'))
    driver_folder = f"{driver.id}_{clean_driver_name}" if clean_driver_name else str(driver.id)

    # Clean file name
    raw_name = os.path.basename(file.filename or "uploaded_file")
    clean_file_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', raw_name)

    # Upload directly to AWS S3 under driver-compliance/{driver_folder}/{clean_file_name}
    file_key, storage_type = storage_service.upload_file(
        file_bytes=content,
        file_name=clean_file_name,
        driver_folder=driver_folder,
        content_type=mime
    )

    doc = DriverDocument(
        driver_id=driver_id,
        document_type_id=document_type_id,
        file_name=raw_name,
        file_key=file_key,
        file_size=file_size,
        mime_type=mime,
        storage_type=storage_type,
        page_number=page_number,
        notes=notes.strip() if notes else None,
        uploaded_by_staff_id=current_staff.id
    )
    db.add(doc)

    record_driver_audit(
        db=db,
        driver_id=driver_id,
        staff=current_staff,
        action_type="DOCUMENT_UPLOAD",
        field_name=f"Document: {doc_type.name}",
        old_value=None,
        new_value=f"{raw_name} (Uploaded)",
        notes=notes
    )

    db.commit()
    db.refresh(doc)

    return DocumentUploadResponse(
        success=True,
        message=f"{doc_type.name} uploaded successfully",
        document=DocumentResponse(
            id=doc.id,
            driver_id=doc.driver_id,
            document_type_id=doc.document_type_id,
            document_type_name=doc_type.name,
            document_type_code=doc_type.code,
            file_name=doc.file_name,
            file_size=doc.file_size,
            mime_type=doc.mime_type,
            page_number=doc.page_number,
            notes=doc.notes,
            storage_type=doc.storage_type,
            uploaded_at=doc.uploaded_at,
            uploaded_by_name=current_staff.full_name
        )
    )

@router.put("/{document_id}/replace", response_model=DocumentUploadResponse)
async def replace_driver_document(
    document_id: int,
    file: UploadFile = File(...),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    doc = db.query(DriverDocument).filter(DriverDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document record not found")

    mime = file.content_type or "application/octet-stream"
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {mime}")

    content = await file.read()
    file_size = len(content)

    old_raw_name = doc.file_name
    doc_type_name = doc.document_type.name if doc.document_type else "Document"

    # Delete old file
    old_key = doc.file_key
    old_storage = doc.storage_type
    try:
        storage_service.delete_file(old_key, old_storage)
    except Exception:
        pass

    driver = db.query(Driver).filter(Driver.id == doc.driver_id).first()
    clean_driver_name = re.sub(r'[^a-zA-Z0-9_\-]', '', driver.full_name.strip().replace(' ', '_')) if driver else ""
    driver_folder = f"{doc.driver_id}_{clean_driver_name}" if clean_driver_name else str(doc.driver_id)

    raw_name = os.path.basename(file.filename or "replaced_file")
    clean_file_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', raw_name)

    file_key, storage_type = storage_service.upload_file(
        file_bytes=content,
        file_name=clean_file_name,
        driver_folder=driver_folder,
        content_type=mime
    )

    doc.file_name = raw_name
    doc.file_key = file_key
    doc.file_size = file_size
    doc.mime_type = mime
    doc.storage_type = storage_type
    if notes is not None:
        doc.notes = notes.strip()
    doc.uploaded_by_staff_id = current_staff.id

    record_driver_audit(
        db=db,
        driver_id=doc.driver_id,
        staff=current_staff,
        action_type="DOCUMENT_REPLACE",
        field_name=f"Document: {doc_type_name}",
        old_value=f"Old file: {old_raw_name}",
        new_value=f"Replaced with: {raw_name}",
        notes=notes
    )

    db.commit()
    db.refresh(doc)

    return DocumentUploadResponse(
        success=True,
        message="Document replaced successfully",
        document=DocumentResponse(
            id=doc.id,
            driver_id=doc.driver_id,
            document_type_id=doc.document_type_id,
            document_type_name=doc.document_type.name if doc.document_type else "",
            document_type_code=doc.document_type.code if doc.document_type else "",
            file_name=doc.file_name,
            file_size=doc.file_size,
            mime_type=doc.mime_type,
            page_number=doc.page_number,
            notes=doc.notes,
            storage_type=doc.storage_type,
            uploaded_at=doc.uploaded_at,
            uploaded_by_name=current_staff.full_name
        )
    )

@router.get("/{document_id}/view")
def view_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    doc = db.query(DriverDocument).filter(DriverDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # If document is in S3, redirect directly to the S3 URL in the new tab
    if doc.storage_type == "s3" and storage_service.s3_client:
        url = storage_service.generate_presigned_url(doc.file_key)
        if url:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=url, status_code=307)

    # Local fallback streaming
    content = storage_service.get_file_content(doc.file_key, doc.storage_type)
    if not content:
        raise HTTPException(status_code=404, detail="Document content could not be retrieved")

    return StreamingResponse(
        io.BytesIO(content),
        media_type=doc.mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{doc.file_name}"',
            "Cache-Control": "max-age=3600"
        }
    )

@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    doc = db.query(DriverDocument).filter(DriverDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    content = storage_service.get_file_content(doc.file_key, doc.storage_type)
    if not content:
        raise HTTPException(status_code=404, detail="Document file content could not be retrieved")

    return StreamingResponse(
        io.BytesIO(content),
        media_type=doc.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{doc.file_name}"',
            "Cache-Control": "no-cache"
        }
    )

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    doc = db.query(DriverDocument).filter(DriverDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        storage_service.delete_file(doc.file_key, doc.storage_type)
    except Exception as e:
        print(f"[Document Deletion Warning]: {e}")

    # Audit log
    doc_name = doc.file_name
    doc_type_name = doc.document_type.name if doc.document_type else "Document"
    record_driver_audit(
        db=db,
        driver_id=doc.driver_id,
        staff=current_staff,
        action_type="DOCUMENT_DELETE",
        field_name=f"Document: {doc_type_name}",
        old_value=doc_name,
        new_value="Deleted from storage"
    )

    db.delete(doc)
    db.commit()
    return {"success": True, "message": "Document deleted successfully"}
