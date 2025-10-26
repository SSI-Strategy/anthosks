"""Abstract storage interface for deployment flexibility."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List


class StorageProvider(ABC):
    """Abstract storage provider interface."""

    @abstractmethod
    def upload_file(self, local_path: Path, remote_path: str) -> str:
        """Upload file and return remote URL/path."""
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: Path) -> Path:
        """Download file to local path."""
        pass

    @abstractmethod
    def list_files(self, prefix: str = "") -> List[str]:
        """List files with optional prefix filter."""
        pass

    @abstractmethod
    def delete_file(self, remote_path: str) -> bool:
        """Delete file."""
        pass

    @abstractmethod
    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists."""
        pass
