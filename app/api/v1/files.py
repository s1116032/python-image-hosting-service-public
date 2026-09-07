from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.file import (
    FileCompleteResponse,
    FileResponse,
    FileUploadUrlCreate,
    FileUploadUrlResponse,
)
from app.services import file_service

router = APIRouter()


@router.post(
    "/files/upload-urls",
    response_model=FileUploadUrlResponse,
    status_code=201,
)
def create_upload_url(
    payload: FileUploadUrlCreate,
    db: Session = Depends(get_db),
):
    return file_service.create_upload_url(db, payload)


@router.get(
    "/files/{file_id}",
    response_model=FileResponse,
)
def get_file(
    file_id: str,
    db: Session = Depends(get_db),
):
    file_obj = file_service.get_file(db, file_id)
    return FileResponse.from_model(file_obj)


@router.post(
    "/files/{file_id}/complete",
    response_model=FileCompleteResponse,
)
def complete_file(
    file_id: str,
    db: Session = Depends(get_db),
):
    file_obj = file_service.complete_upload(db, file_id)
    return FileCompleteResponse.from_model(file_obj)
