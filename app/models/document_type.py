from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class DocumentType(Base):
    __tablename__ = "dc_document_types"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    requires_expiry = Column(Boolean, default=False, nullable=False)
    requires_issue_date = Column(Boolean, default=False, nullable=False)
    is_mandatory = Column(Boolean, default=False, nullable=False)
    council_tag = Column(String(50), default="ALL", nullable=False) # ALL, SCC, DCC, NONE
    is_custom = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    documents = relationship("DriverDocument", back_populates="document_type", cascade="all, delete-orphan")
