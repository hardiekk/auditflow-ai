from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import get_settings


class FileStorageProvider(ABC):
    @abstractmethod
    def put(self, key: str, data: bytes, content_type: str = "application/pdf") -> str: ...

    @abstractmethod
    def get(self, key: str) -> bytes: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...


class LocalFileStorage(FileStorageProvider):
    def __init__(self, root: str | None = None) -> None:
        self.root = Path(root or get_settings().storage_local_path)
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, key: str, data: bytes, content_type: str = "application/pdf") -> str:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def get(self, key: str) -> bytes:
        return (self.root / key).read_bytes()

    def exists(self, key: str) -> bool:
        return (self.root / key).exists()


class S3CompatibleStorage(FileStorageProvider):
    """Interface for future S3-compatible object storage. Not wired in MVP Docker."""

    def put(self, key: str, data: bytes, content_type: str = "application/pdf") -> str:
        raise NotImplementedError("S3 storage is coming soon; use STORAGE_BACKEND=local")

    def get(self, key: str) -> bytes:
        raise NotImplementedError("S3 storage is coming soon")

    def exists(self, key: str) -> bool:
        raise NotImplementedError("S3 storage is coming soon")


def get_storage() -> FileStorageProvider:
    settings = get_settings()
    if settings.storage_backend == "s3":
        return S3CompatibleStorage()
    return LocalFileStorage()
