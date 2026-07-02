import base64
import inspect
import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from schemas.file_attachment import DownloadFileResponse, UploadFileResponse
from utils.db.file_attachment_repository import (
    fetch_file_attachment,
    insert_file_attachment,
)


DEFAULT_MAX_UPLOAD_FILE_SIZE_MB = 25


def _allowed_extensions() -> set[str] | None:
    allowed_extensions = os.getenv("ALLOWED_FILE_EXTENSIONS", "").strip()
    if not allowed_extensions:
        return None

    return {
        extension.strip().lower().lstrip(".")
        for extension in allowed_extensions.split(",")
        if extension.strip()
    }


def _max_upload_size_bytes() -> int:
    max_size_mb = os.getenv("MAX_UPLOAD_FILE_SIZE_MB")
    if not max_size_mb:
        return DEFAULT_MAX_UPLOAD_FILE_SIZE_MB * 1024 * 1024

    return int(max_size_mb) * 1024 * 1024


def _get_extension(file_name: str) -> str:
    return Path(file_name).suffix.lower().lstrip(".")


def _safe_file_name(file_name: str | None) -> str:
    if not file_name:
        return "uploaded_file"

    return Path(file_name).name


def _validate_file(file_name: str, file_content: bytes) -> None:
    extension = _get_extension(file_name)
    allowed_extensions = _allowed_extensions()

    if allowed_extensions is not None and extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid File extension")

    if len(file_content) > _max_upload_size_bytes():
        max_size_mb = _max_upload_size_bytes() // 1024 // 1024
        raise HTTPException(
            status_code=400,
            detail=f"File size cannot be more than {max_size_mb} MB",
        )


async def _read_blob_content(blob_value) -> bytes:
    if blob_value is None:
        return b""

    if isinstance(blob_value, bytes):
        return blob_value

    if isinstance(blob_value, bytearray):
        return bytes(blob_value)

    if hasattr(blob_value, "read"):
        content = blob_value.read()
        if inspect.isawaitable(content):
            content = await content
        return content

    return bytes(blob_value)


async def upload_file(
    *,
    file: UploadFile,
    user_name: str | None,
    file_type: str | None,
) -> UploadFileResponse:
    original_file_name = _safe_file_name(file.filename)
    file_content = await file.read()
    _validate_file(original_file_name, file_content)

    file_attachment_id = str(uuid.uuid4())
    stored_file_name = f"{file_attachment_id}_{original_file_name}"

    await insert_file_attachment(
        user_name=user_name,
        file_type=file_type or file.content_type,
        file_name=stored_file_name,
        file_attachment_id=file_attachment_id,
        file_content=file_content,
    )
    print(f"File uploaded successfully: {stored_file_name} (ID: {file_attachment_id})")
    return UploadFileResponse(
        fileName=stored_file_name,
        fileAttachmentId=file_attachment_id,
        Success="File Uploaded Successfully",
    )


async def download_file(file_attachment_id: str) -> DownloadFileResponse:
    file_record = await fetch_file_attachment(file_attachment_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    file_name = file_record.get("FILE_NAME") or file_record.get("file_name")
    blob_value = file_record.get("FILE_CONTENT") or file_record.get("file_content")
    file_content = await _read_blob_content(blob_value)

    return DownloadFileResponse(
        fileName=file_name,
        fileContent=base64.b64encode(file_content).decode("utf-8"),
    )
