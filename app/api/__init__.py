from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.staff import router as staff_router
from app.api.drivers import router as drivers_router
from app.api.documents import router as documents_router
from app.api.document_types import router as document_types_router
from app.api.dashboard import router as dashboard_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(staff_router)
api_router.include_router(drivers_router)
api_router.include_router(documents_router)
api_router.include_router(document_types_router)
api_router.include_router(dashboard_router)
