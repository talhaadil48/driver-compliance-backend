from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.core.database import Base

class CouncilRequirement(Base):
    __tablename__ = "dc_council_requirements"

    id = Column(Integer, primary_key=True, index=True)
    council_code = Column(String(50), unique=True, index=True, nullable=False) # e.g. "SCC", "DCC"
    council_name = Column(String(255), nullable=False) # e.g. "Surrey County Council", "Devon County Council"
    description = Column(Text, nullable=True)
    
    # Comma-separated or JSON list of required expiry field keys:
    # e.g., '["scc_badge_expiry", "dbs_update_service_expiry", "safeguarding_expiry", "first_aid_expiry"]'
    required_expiry_fields = Column(Text, nullable=False, default="[]")

    # Comma-separated or JSON list of required document type codes:
    # e.g., '["scc_badge", "dbs_certificate", "dbs_update_service_proof", "safeguarding_certificate", "first_aid_certificate"]'
    required_document_codes = Column(Text, nullable=False, default="[]")

    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
