from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class DriverAuditLog(Base):
    __tablename__ = "dc_driver_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("dc_drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey("dc_staff_users.id", ondelete="SET NULL"), nullable=True, index=True)
    staff_name = Column(String(255), nullable=False)
    action_type = Column(String(50), nullable=False) # FIELD_UPDATE, DOCUMENT_UPLOAD, DOCUMENT_REPLACE, DOCUMENT_DELETE, DRIVER_CREATED
    field_name = Column(String(150), nullable=False) # e.g. "Phone Number", "Driving Licence Expiry", "Document: Taxi Badge"
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    driver = relationship("Driver", backref="audit_logs")
    staff = relationship("StaffUser")
