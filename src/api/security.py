"""Security helpers for API route authorization and upload handling."""

from pathlib import Path
import re
import uuid
from typing import Any

from fastapi import HTTPException, status

CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def user_owner_id(user: dict[str, Any]) -> str:
    owner_id = user.get("oid") or user.get("sub") or user.get("email") or user.get("preferred_username")
    if not owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user is missing a stable owner identifier",
        )
    return str(owner_id)


def user_email(user: dict[str, Any]) -> str | None:
    email = user.get("email") or user.get("preferred_username")
    return str(email).lower() if email else None


def validate_upload_filename(filename: str | None) -> str:
    if not filename:
        raise HTTPException(status_code=400, detail="Uploaded file must include a filename")
    if "/" in filename or "\\" in filename or CONTROL_CHARS.search(filename):
        raise HTTPException(status_code=400, detail="Uploaded filename contains invalid characters")

    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are accepted")
    return suffix


def contained_upload_path(input_path: Path, file_suffix: str) -> Path:
    base_path = Path(input_path).resolve()
    base_path.mkdir(parents=True, exist_ok=True)
    destination = (base_path / f"{uuid.uuid4().hex}{file_suffix}").resolve()
    try:
        destination.relative_to(base_path)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid upload destination")
    return destination
