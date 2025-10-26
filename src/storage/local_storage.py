"""Local file system storage implementation."""

from pathlib import Path
from typing import List
import shutil
import logging

from .base import StorageProvider

logger = logging.getLogger(__name__)


class LocalStorage(StorageProvider):
    """Local file system storage."""

    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def upload_file(self, local_path: Path, remote_path: str) -> str:
        """Copy file to storage location."""
        dest = self.base_path / remote_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_path, dest)
        logger.info(f"Uploaded: {local_path} -> {dest}")
        return str(dest)

    def download_file(self, remote_path: str, local_path: Path) -> Path:
        """Copy file from storage."""
        source = self.base_path / remote_path
        shutil.copy2(source, local_path)
        logger.info(f"Downloaded: {source} -> {local_path}")
        return local_path

    def list_files(self, prefix: str = "") -> List[str]:
        """List files matching prefix."""
        pattern = f"{prefix}*" if prefix else "*"
        files = list(self.base_path.glob(pattern))
        return [str(f.relative_to(self.base_path)) for f in files if f.is_file()]

    def delete_file(self, remote_path: str) -> bool:
        """Delete file."""
        file_path = self.base_path / remote_path
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted: {file_path}")
            return True
        return False

    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists."""
        return (self.base_path / remote_path).exists()
