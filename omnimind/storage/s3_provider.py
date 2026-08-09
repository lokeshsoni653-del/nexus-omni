"""
OmniMind AI — S3 / Supabase Cloud Storage Provider
"""
import os
import shutil
import logging
from typing import Optional
from config import settings
from omnimind.storage.base import StorageProvider

logger = logging.getLogger("omnimind.storage.s3")

try:
    import boto3
    from botocore.config import Config as BotoConfig
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class S3StorageProvider(StorageProvider):
    """AWS S3 and Supabase S3-compatible cloud storage provider."""

    def __init__(self):
        self.bucket_name = settings.S3_BUCKET_NAME
        self.enabled = settings.USE_S3_STORAGE and HAS_BOTO3 and bool(settings.AWS_ACCESS_KEY_ID)

        if self.enabled:
            client_kwargs = {
                "service_name": "s3",
                "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
                "region_name": settings.AWS_REGION,
            }
            if settings.S3_ENDPOINT_URL:
                client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

            self.s3_client = boto3.client(**client_kwargs)
            logger.info(f"S3 Storage Provider initialized — bucket: '{self.bucket_name}'.")
        else:
            self.s3_client = None
            logger.info("S3 Storage disabled or unconfigured. Using local disk storage fallback.")

    def upload_file(self, file_bytes: bytes, file_name: str, content_type: str = "application/pdf") -> str:
        """Upload file to S3 bucket or save to local upload directory."""
        if self.enabled and self.s3_client:
            key = f"documents/{file_name}"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_bytes,
                ContentType=content_type,
            )
            logger.info(f"Uploaded file to S3: s3://{self.bucket_name}/{key}")
            return key
        else:
            # Fallback to local disk
            local_path = os.path.join(settings.UPLOAD_DIR, file_name)
            with open(local_path, "wb") as f:
                f.write(file_bytes)
            logger.info(f"Saved file to local disk: {local_path}")
            return local_path

    def download_file(self, storage_key: str, dest_path: str) -> str:
        """Download remote S3 file to local disk path for RAG ingestion."""
        if self.enabled and self.s3_client and not os.path.exists(storage_key):
            logger.info(f"Downloading s3://{self.bucket_name}/{storage_key} -> {dest_path}")
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            self.s3_client.download_file(self.bucket_name, storage_key, dest_path)
            return dest_path
        else:
            # If already a local path, ensure destination exists or copy
            if os.path.exists(storage_key) and storage_key != dest_path:
                shutil.copy(storage_key, dest_path)
                return dest_path
            return storage_key

    def get_public_url(self, storage_key: str) -> str:
        """Return download URL for a file key."""
        if self.enabled and self.s3_client:
            if settings.S3_ENDPOINT_URL:
                return f"{settings.S3_ENDPOINT_URL.rstrip('/')}/{self.bucket_name}/{storage_key}"
            return f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{storage_key}"
        return f"/uploads/{os.path.basename(storage_key)}"


# Singleton factory helper
_storage_instance = None


def get_storage_provider() -> StorageProvider:
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = S3StorageProvider()
    return _storage_instance
