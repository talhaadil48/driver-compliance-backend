from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.staff import StaffUser

db = SessionLocal()
try:
    admin = db.query(StaffUser).filter(StaffUser.email == "admin@company.com").first()
    if admin:
        admin.hashed_password = get_password_hash("admin123")
        db.commit()
        print(f"Password updated successfully for {admin.email} to 'admin123'")
    else:
        # Create if not exists
        admin = StaffUser(
            email="admin@company.com",
            full_name="Company Compliance Admin",
            hashed_password=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("Created admin account admin@company.com with password 'admin123'")
finally:
    db.close()
