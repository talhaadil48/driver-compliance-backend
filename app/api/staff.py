from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_staff, require_admin
from app.core.security import get_password_hash
from app.models.staff import StaffUser
from app.schemas.staff import StaffResponse, StaffCreate, StaffUpdate

router = APIRouter(prefix="/staff", tags=["Staff Management"])

@router.get("", response_model=List[StaffResponse])
def list_staff_members(
    db: Session = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    return db.query(StaffUser).order_by(StaffUser.id.asc()).all()

@router.post("", response_model=StaffResponse)
def create_staff_member(
    data: StaffCreate,
    db: Session = Depends(get_db),
    admin: StaffUser = Depends(require_admin)
):
    existing = db.query(StaffUser).filter(StaffUser.email == data.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Staff account with this email already exists")

    new_staff = StaffUser(
        email=data.email.lower().strip(),
        full_name=data.full_name.strip(),
        hashed_password=get_password_hash(data.password),
        role=data.role,
        is_active=True
    )
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)
    return new_staff

@router.patch("/{staff_id}", response_model=StaffResponse)
def update_staff_member(
    staff_id: int,
    data: StaffUpdate,
    db: Session = Depends(get_db),
    admin: StaffUser = Depends(require_admin)
):
    staff = db.query(StaffUser).filter(StaffUser.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    if data.full_name is not None:
        staff.full_name = data.full_name.strip()
    if data.role is not None:
        staff.role = data.role
    if data.is_active is not None:
        staff.is_active = data.is_active
    if data.password:
        staff.hashed_password = get_password_hash(data.password)

    db.commit()
    db.refresh(staff)
    return staff

@router.delete("/{staff_id}")
def delete_staff_member(
    staff_id: int,
    db: Session = Depends(get_db),
    admin: StaffUser = Depends(require_admin)
):
    if admin.id == staff_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own staff account")

    staff = db.query(StaffUser).filter(StaffUser.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    db.delete(staff)
    db.commit()
    return {"success": True, "message": "Staff member deleted successfully"}
