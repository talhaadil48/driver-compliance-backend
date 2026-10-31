from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class DocumentResponse(BaseModel):
    id: int
    driver_id: int
    document_type_id: int
    document_type_name: str
    document_type_code: str
    file_name: str
    file_size: int
    mime_type: str
    page_number: int = 1
    notes: Optional[str] = None
    storage_type: str
    uploaded_at: datetime
    uploaded_by_name: Optional[str] = None

    class Config:
        from_attributes = True

class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    document: DocumentResponse

class PresignUploadRequest(BaseModel):
    file_name: str
    document_type_id: int
    mime_type: str = "application/pdf"
    file_size: int

class PresignUploadResponse(BaseModel):
    upload_url: str
    file_key: str
    file_name: str
    storage_type: str = "s3"

class ConfirmUploadRequest(BaseModel):
    document_type_id: int
    file_name: str
    file_key: str
    file_size: int
    mime_type: str
    storage_type: str = "s3"
    notes: Optional[str] = None

class PresignReplaceRequest(BaseModel):
    file_name: str
    mime_type: str = "application/pdf"
    file_size: int

class ConfirmReplaceRequest(BaseModel):
    file_name: str
    file_key: str
    file_size: int
    mime_type: str
    storage_type: str = "s3"
    notes: Optional[str] = None
