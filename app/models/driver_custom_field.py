from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class DriverCustomField(Base):
    __tablename__ = "dc_driver_custom_fields"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("dc_drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(255), nullable=False)
    field_type = Column(String(50), default="date", nullable=False) # date or text
    date_value = Column(Date, nullable=True)
    text_value = Column(Text, nullable=True)
    is_required = Column(Boolean, default=False, nullable=False)
    document_type_id = Column(Integer, ForeignKey("dc_document_types.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    driver = relationship("Driver")
    document_type = relationship("DocumentType")
