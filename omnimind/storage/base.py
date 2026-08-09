"""
OmniMind AI — Abstract Storage Provider Interface
"""
from abc import ABC, abstractmethod
from typing import Optional


class StorageProvider(ABC):
    """Abstract interface for cloud document storage (AWS S3, Supabase Storage, Local)."""

    @abstractmethod
    def upload_file(self, file_bytes: bytes, file_name: str, content_type: str = "application/pdf") -> str:
        """Upload file bytes to storage and return remote key / path."""
        pass

    @abstractmethod
    def download_file(self, storage_key: str, dest_path: str) -> str:
        """Download remote storage file to local disk path."""
        pass

    @abstractmethod
    def get_public_url(self, storage_key: str) -> str:
        """Get accessible download URL for a file key."""
        pass
