from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class DriverDocument(Base):
    __tablename__ = "dc_driver_documents"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("dc_drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type_id = Column(Integer, ForeignKey("dc_document_types.id", ondelete="CASCADE"), nullable=False, index=True)
    
    file_name = Column(String(255), nullable=False)
    file_key = Column(String(500), nullable=False) # S3 Key or local path
    file_size = Column(Integer, nullable=False) # In bytes
    mime_type = Column(String(100), nullable=False)
    storage_type = Column(String(50), default="s3", nullable=False) # s3 or local
    
    # Metadata for multi-page documents (e.g. DBS certificate multi-pages)
    page_number = Column(Integer, default=1, nullable=False)
    notes = Column(Text, nullable=True)

    uploaded_by_staff_id = Column(Integer, ForeignKey("dc_staff_users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    driver = relationship("Driver", back_populates="documents")
    document_type = relationship("DocumentType", back_populates="documents")
    uploaded_by = relationship("StaffUser")
