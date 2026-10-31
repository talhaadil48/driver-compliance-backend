from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_staff
from app.core.security import verify_password, create_access_token
from app.models.staff import StaffUser
from app.schemas.staff import StaffLoginRequest, StaffTokenResponse, StaffResponse

router = APIRouter(prefix="/auth", tags=["Staff Authentication"])

@router.post("/login", response_model=StaffTokenResponse)
def staff_login(creds: StaffLoginRequest, db: Session = Depends(get_db)):
    staff = db.query(StaffUser).filter(StaffUser.email == creds.email.lower().strip()).first()
    if not staff or not verify_password(creds.password, staff.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not staff.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff account has been deactivated. Contact your compliance administrator."
        )

    token = create_access_token(subject=staff.id)
    return StaffTokenResponse(
        access_token=token,
        token_type="bearer",
        staff=StaffResponse.model_validate(staff)
    )

@router.get("/me", response_model=StaffResponse)
def get_current_staff_profile(current_staff: StaffUser = Depends(get_current_staff)):
    return StaffResponse.model_validate(current_staff)
