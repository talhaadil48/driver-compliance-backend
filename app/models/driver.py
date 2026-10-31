from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class Driver(Base):
    __tablename__ = "dc_drivers"

    id = Column(Integer, primary_key=True, index=True)
    
    # 1. Driver Full Name
    full_name = Column(String(255), nullable=False, index=True)
    # Profile Type (Driver or Passenger)
    type = Column(String(50), default="Driver", nullable=False, index=True)
    # Driver Callsign / ID
    callsign = Column(String(50), nullable=True, index=True)
    # 2. Date of Birth
    dob = Column(Date, nullable=True)
    # 3. National Insurance Number
    national_insurance_number = Column(String(100), nullable=True, index=True)
    
    # Text identifiers
    # 7. DBS Certificate Number
    dbs_certificate_number = Column(String(100), nullable=True)
    # 8. DBS Update Service Reference
    dbs_update_service_reference = Column(String(100), nullable=True)

    # Optional contact & metadata
    email = Column(String(255), nullable=True)
    phone = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    council_affiliation = Column(String(50), default="BOTH", nullable=False) # SCC, DCC, BOTH, NONE

    # Required & Optional Expiry Dates
    driving_licence_expiry = Column(Date, nullable=True)
    passport_expiry = Column(Date, nullable=True)
    driver_id_badge_expiry = Column(Date, nullable=True)
    dbs_update_service_expiry = Column(Date, nullable=True)
    safeguarding_expiry = Column(Date, nullable=True)
    first_aid_expiry = Column(Date, nullable=True)
    autism_awareness_expiry = Column(Date, nullable=True)
    autism_awareness_expiry_enabled = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    documents = relationship("DriverDocument", back_populates="driver", cascade="all, delete-orphan")
