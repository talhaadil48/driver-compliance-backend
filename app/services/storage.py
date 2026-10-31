import os
import shutil
from typing import Optional, Tuple
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings

class StorageService:
    def __init__(self):
        self.bucket_name = settings.AWS_S3_BUCKET_NAME
        self.region = settings.AWS_REGION
        self.project_folder = settings.AWS_S3_PROJECT_FOLDER # e.g. "driver-compliance" - NEVER "accident-claims"
        self.local_dir = settings.LOCAL_STORAGE_DIR

        self.s3_client = None
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            try:
                self.s3_client = boto3.client(
                    "s3",
                    region_name=self.region,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                )
            except Exception as e:
                print(f"[Storage Service Warning] Could not initialize AWS S3 client: {e}")

        # Ensure local directory exists for fallback or local files
        try:
            os.makedirs(self.local_dir, exist_ok=True)
        except Exception:
            pass

    def upload_file(
        self,
        file_bytes: bytes,
        file_name: str,
        driver_folder: str,
        content_type: str = "application/pdf"
    ) -> Tuple[str, str]:
        """
        Uploads file directly to AWS S3 inside the driver's folder:
        driver-compliance/{driver_folder}/{file_name}
        Returns tuple of (file_key, storage_type).
        """
        safe_key = f"{self.project_folder}/{driver_folder}/{file_name}"

        if self.s3_client:
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=safe_key,
                    Body=file_bytes,
                    ContentType=content_type,
                )
                return safe_key, "s3"
            except Exception as e:
                print(f"[Storage S3 Upload Error] Falling back to local storage: {e}")

        # Local storage fallback
        local_path = os.path.join(self.local_dir, self.project_folder, str(driver_folder))
        os.makedirs(local_path, exist_ok=True)
        file_path = os.path.join(local_path, file_name)
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        return safe_key, "local"

    def get_file_content(self, file_key: str, storage_type: str = "s3") -> Optional[bytes]:
        """
        Retrieves file bytes from S3 or local storage.
        """
        if storage_type == "s3" and self.s3_client:
            try:
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)
                return response["Body"].read()
            except Exception as e:
                print(f"[Storage S3 Download Error]: {e}")

        # Try local storage
        candidate_paths = [
            os.path.join(self.local_dir, file_key),
            os.path.join("uploads", file_key),
            os.path.join("backend", "uploads", file_key),
            os.path.join(os.path.dirname(os.path.abspath(self.local_dir)), file_key),
        ]
        for p in candidate_paths:
            if os.path.exists(p) and os.path.isfile(p):
                with open(p, "rb") as f:
                    return f.read()

        return None

    def delete_file(self, file_key: str, storage_type: str = "s3") -> bool:
        """
        Deletes file from S3 or local storage.
        """
        if not file_key.startswith(f"{self.project_folder}/"):
            print(f"[Storage Security Alert] Attempted to delete key outside project prefix: {file_key}")
            return False

        if storage_type == "s3" and self.s3_client:
            try:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
                return True
            except Exception as e:
                print(f"[Storage S3 Delete Error]: {e}")

        candidate_paths = [
            os.path.join(self.local_dir, file_key),
            os.path.join("uploads", file_key),
            os.path.join("backend", "uploads", file_key),
        ]
        for p in candidate_paths:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception as e:
                    print(f"[Storage Local Delete Error]: {e}")

        return True

    def generate_presigned_url(self, file_key: str, expiration: int = 3600) -> Optional[str]:
        if self.s3_client:
            try:
                url = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": file_key},
                    ExpiresIn=expiration,
                )
                return url
            except Exception as e:
                print(f"[Presigned URL Error]: {e}")
        return None

    def generate_presigned_upload_url(self, file_key: str, content_type: str = "application/pdf", expiration: int = 3600) -> Optional[str]:
        if self.s3_client:
            try:
                url = self.s3_client.generate_presigned_url(
                    "put_object",
                    Params={
                        "Bucket": self.bucket_name,
                        "Key": file_key,
                        "ContentType": content_type
                    },
                    ExpiresIn=expiration,
                )
                return url
            except Exception as e:
                print(f"[Presigned Upload URL Error]: {e}")
        return None

storage_service = StorageService()
