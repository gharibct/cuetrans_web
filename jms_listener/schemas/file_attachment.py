from pydantic import BaseModel


class DownloadFileRequest(BaseModel):
    file_attachment_id: str


class DownloadFileResponse(BaseModel):
    fileName: str
    fileContent: str


class UploadFileResponse(BaseModel):
    fileName: str | None = None
    fileAttachmentId: str | None = None
    Success: str | None = None
    Failure: str | None = None
