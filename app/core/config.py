import os
import json
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "Drivers Compliance Management System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Database
    DATABASE_URL: str = "sqlite:///./driver_compliance.db"
    DB_SCHEMA: str = "driver_compliance"

    # AWS S3 Storage
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET_NAME: str = "gogreen11"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_PROJECT_FOLDER: str = "driver-compliance"

    # Local fallback storage
    LOCAL_STORAGE_DIR: str = "./uploads"

    # Security
    JWT_SECRET_KEY: str = "drivers-compliance-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Initial Admin Seed
    INITIAL_ADMIN_EMAIL: str = "admin@company.com"
    INITIAL_ADMIN_PASSWORD: str = "AdminPassword123!"
    INITIAL_ADMIN_NAME: str = "Company Compliance Admin"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
