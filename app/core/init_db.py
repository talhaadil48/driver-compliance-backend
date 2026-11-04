from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.core.database import Base, engine, SessionLocal
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.staff import StaffUser
from app.models.document_type import DocumentType
from app.models.driver import Driver

DEFAULT_DOCUMENT_TYPES = [
    {
        "code": "driving_licence",
        "name": "Driving Licence",
        "description": "Full UK driving licence (front and back)",
        "requires_expiry": False,
        "requires_issue_date": False,
        "is_mandatory": True,
        "council_tag": "NONE"
    },
    {
        "code": "passport",
        "name": "Passport",
        "description": "Valid passport biometric page",
        "requires_expiry": False,
        "requires_issue_date": False,
        "is_mandatory": True,
        "council_tag": "NONE"
    },
    {
        "code": "driver_id_badge",
        "name": "Driver ID Badge",
        "description": "Official driver photo ID badge",
        "requires_expiry": False,
        "requires_issue_date": False,
        "is_mandatory": True,
        "council_tag": "NONE"
    },
    {
        "code": "dbs_update_service_proof",
        "name": "DBS Update Service Proof",
        "description": "Proof of active registration with DBS Update Service",
        "requires_expiry": True,
        "requires_issue_date": False,
        "is_mandatory": True,
        "council_tag": "NONE"
    },
    {
        "code": "safeguarding_certificate",
        "name": "Safeguarding Certificate",
        "description": "Child and adult safeguarding training certification",
        "requires_expiry": True,
        "requires_issue_date": True,
        "is_mandatory": True,
        "council_tag": "NONE"
    },
    {
        "code": "first_aid_certificate",
        "name": "First Aid Certificate",
        "description": "Emergency First Aid at Work certificate",
        "requires_expiry": True,
        "requires_issue_date": True,
        "is_mandatory": True,
        "council_tag": "NONE"
    },
    {
        "code": "autism_awareness_certificate",
        "name": "Autism Awareness Certificate",
        "description": "Autism and neurodiversity awareness certificate",
        "requires_expiry": False,
        "requires_issue_date": False,
        "is_mandatory": False,
        "council_tag": "NONE"
    },
    {
        "code": "dbs_certificate",
        "name": "DBS Certificate",
        "description": "Enhanced DBS Certificate (multi-page support)",
        "requires_expiry": False,
        "requires_issue_date": True,
        "is_mandatory": True,
        "council_tag": "NONE"
    },
    {
        "code": "proof_of_address",
        "name": "Proof of Address",
        "description": "Recent utility bill or bank statement (within 3 months)",
        "requires_expiry": False,
        "requires_issue_date": True,
        "is_mandatory": True,
        "council_tag": "NONE"
    },
    {
        "code": "proof_of_national_insurance",
        "name": "Proof of National Insurance Number",
        "description": "HMRC letter, P45, P60 or official NI card",
        "requires_expiry": False,
        "requires_issue_date": False,
        "is_mandatory": True,
        "council_tag": "NONE"
    },
    {
        "code": "passport_size_photograph",
        "name": "Passport-size Photograph",
        "description": "Standard recent passport-style driver photograph",
        "requires_expiry": False,
        "requires_issue_date": False,
        "is_mandatory": True,
        "council_tag": "NONE"
    }
]

def init_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed initial admin staff user only if no admin account exists
        existing_admin = db.query(StaffUser).filter(StaffUser.role == "admin").first()
        if not existing_admin:
            admin_email = settings.INITIAL_ADMIN_EMAIL.lower().strip()
            existing_user = db.query(StaffUser).filter(StaffUser.email == admin_email).first()
            if not existing_user:
                admin_user = StaffUser(
                    email=admin_email,
                    full_name=settings.INITIAL_ADMIN_NAME,
                    hashed_password=get_password_hash(settings.INITIAL_ADMIN_PASSWORD),
                    role="admin",
                    is_active=True
                )
                db.add(admin_user)
                print(f"[Init DB] Created default admin account: {admin_email}")

        # Seed default document types
        for dt_data in DEFAULT_DOCUMENT_TYPES:
            existing_dt = db.query(DocumentType).filter(DocumentType.code == dt_data["code"]).first()
            if not existing_dt:
                new_dt = DocumentType(
                    code=dt_data["code"],
                    name=dt_data["name"],
                    description=dt_data["description"],
                    requires_expiry=dt_data["requires_expiry"],
                    requires_issue_date=dt_data["requires_issue_date"],
                    is_mandatory=dt_data["is_mandatory"],
                    council_tag="NONE",
                    is_custom=False
                )
                db.add(new_dt)

        db.commit()
        print("[Init DB] Database initialized successfully.")
    except Exception as e:
        db.rollback()
        print(f"[Init DB Error]: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
