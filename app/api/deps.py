import time
from typing import Generator, Optional, Dict, Tuple
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.staff import StaffUser

security = HTTPBearer(auto_error=False)

# In-memory cache for authenticated staff to eliminate WAN round trips on every request
_STAFF_CACHE: Dict[int, Tuple[StaffUser, float]] = {}
CACHE_TTL_SECONDS = 60.0

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_staff(
    auth_creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> StaffUser:
    raw_token = auth_creds.credentials if (auth_creds and auth_creds.credentials) else token
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required. This is a staff-only system.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(raw_token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    staff_id = payload["sub"]
    try:
        staff_id_int = int(staff_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    now = time.time()
    cached = _STAFF_CACHE.get(staff_id_int)
    if cached and (now - cached[1]) < CACHE_TTL_SECONDS:
        return cached[0]

    staff = db.query(StaffUser).filter(StaffUser.id == staff_id_int).first()
    if not staff or not staff.is_active:
        _STAFF_CACHE.pop(staff_id_int, None)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Staff account is disabled or does not exist",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db.expunge(staff)
    _STAFF_CACHE[staff_id_int] = (staff, now)
    return staff

def require_admin(current_staff: StaffUser = Depends(get_current_staff)) -> StaffUser:
    if current_staff.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required for this operation"
        )
    return current_staff
