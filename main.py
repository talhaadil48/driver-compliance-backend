import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.init_db import init_database
from app.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables and seed data exist
    print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}...")
    init_database()
    yield
    print("Shutting down application...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Staff-Only Drivers Compliance and Document Management System",
    lifespan=lifespan
)

# CORS Middleware
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount local uploads for dev fallback
try:
    upload_dir = "/tmp/uploads" if os.environ.get("VERCEL") == "1" else settings.LOCAL_STORAGE_DIR
    os.makedirs(upload_dir, exist_ok=True)
    app.mount("/local-files", StaticFiles(directory=upload_dir), name="local_files")
except Exception as e:
    print(f"[Notice] Local storage mount skipped: {e}")

@app.get("/")
def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "access": "Staff Only - Internal Company Portal",
        "api_docs": "/docs"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "storage": "s3" if (settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY) else "local_fallback",
        "bucket": settings.AWS_S3_BUCKET_NAME,
        "s3_project_folder": settings.AWS_S3_PROJECT_FOLDER
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
