import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from schemas.file_attachment import (
    DownloadFileRequest,
    DownloadFileResponse,
    UploadFileResponse,
)
from services.file_attachment_service import download_file, upload_file


router = APIRouter(tags=["File Handlers"])
logger = logging.getLogger(__name__)


@router.post(
    "/uploadFile",
    response_model=UploadFileResponse,
    response_model_exclude_none=True,
)
async def upload_file_endpoint(
    file: UploadFile = File(...),
    filePath: str | None = Form(None),
    userName: str | None = Form(None),
    fileType: str | None = Form(None),
):
    _ = filePath
    try:
        return await upload_file(
            file=file,
            user_name=userName,
            file_type=fileType,
        )
    except HTTPException as exc:
        logger.error("Error uploading file: %s", exc.detail)
        return UploadFileResponse(Failure=str(exc.detail))
    except Exception as exc:
        logger.error("Error uploading file: %s", exc)
        return UploadFileResponse(Failure=str(exc))


@router.post("/downloadFile", response_model=DownloadFileResponse)
async def download_file_endpoint(request: DownloadFileRequest):
    return await download_file(request.file_attachment_id)
