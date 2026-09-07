import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import (
    AppError,
    ConflictError,
    FileTooLargeError,
    ResourceNotFoundError,
    UnsupportedContentTypeError,
    UploadObjectNotFoundError,
)
from app.models.file import File, FileStatus
from app.schemas.file import FileUploadUrlCreate, FileUploadUrlResponse
from app.services.filetype_service import filetype_service
from app.services.s3_service import s3_service

settings = get_settings()
logger = logging.getLogger(__name__)


def _build_s3_key(filename: str) -> str:
    """
    產生 S3 key。

    格式：
    files/2026/06/17/{uuid}.{ext}
    """

    suffix = Path(filename).suffix.lower()

    if suffix:
        suffix = f".{suffix.lstrip('.')}"

    now = datetime.now(timezone.utc)

    return f"files/{now:%Y/%m/%d}/{uuid.uuid4()}{suffix}"


def _validate_magic_numbers(file_obj: File) -> None:
    """
    從 S3 讀取檔案前 2KB，並用 filetype 驗證真實 MIME Type。

    在 mock 模式下，如果沒有真實檔案內容，會略過驗證。
    """

    if not settings.validate_magic_bytes:
        logger.info(
            "Magic byte validation disabled: file_id=%s",
            file_obj.id,
        )
        return

    first_bytes = s3_service.get_object_first_bytes(
        file_obj.s3_key,
        settings.magic_bytes_limit,
    )

    if settings.use_mock_aws and not first_bytes:
        logger.info(
            "Mock mode: skip real magic number validation: file_id=%s",
            file_obj.id,
        )
        return

    filetype_service.validate_magic_bytes(
        first_bytes,
        file_obj.content_type,
    )


def get_file(db: Session, file_id: str) -> File:
    file_obj = db.get(File, file_id)

    if not file_obj:
        raise ResourceNotFoundError("File not found")

    return file_obj


def create_upload_url(
    db: Session,
    payload: FileUploadUrlCreate,
) -> FileUploadUrlResponse:
    """
    建立上傳簽章。

    流程：
    1. 驗證 content type
    2. 驗證檔案大小
    3. 產生 S3 key
    4. 建立 DB 紀錄，狀態為 pending
    5. 產生 S3 presigned upload URL

    注意：
    這裡的 content_type 只是客户端宣告值，
    真正內容會在 complete 階段用 magic number 二次驗證。
    """

    if payload.content_type not in settings.allowed_content_type_list:
        allowed = ", ".join(settings.allowed_content_type_list)
        raise UnsupportedContentTypeError(
            f"Unsupported content type: {payload.content_type}. "
            f"Allowed types: {allowed}."
        )

    if payload.size_bytes > settings.max_file_size_bytes:
        raise FileTooLargeError(
            f"File size exceeds limit: {settings.max_file_size_mb} MB."
        )

    s3_key = _build_s3_key(payload.filename)
    cloudfront_url = s3_service.build_cloudfront_url(s3_key)

    file_obj = File(
        original_filename=payload.filename,
        s3_key=s3_key,
        content_type=payload.content_type,
        size_bytes=payload.size_bytes,
        upload_status=FileStatus.PENDING,
        cloudfront_url=cloudfront_url,
    )

    db.add(file_obj)
    db.commit()
    db.refresh(file_obj)

    presigned = s3_service.generate_presigned_upload(
        s3_key=file_obj.s3_key,
        content_type=file_obj.content_type,
        size_bytes=file_obj.size_bytes,
        expires_in=settings.presigned_url_expires_seconds,
    )

    logger.info(
        "Created presigned upload URL: "
        "file_id=%s s3_key=%s content_type=%s size_bytes=%s",
        file_obj.id,
        file_obj.s3_key,
        file_obj.content_type,
        file_obj.size_bytes,
    )

    return FileUploadUrlResponse(
        file_id=file_obj.id,
        original_filename=file_obj.original_filename,
        s3_key=file_obj.s3_key,
        upload_url=presigned.get("url", ""),
        upload_fields=presigned.get("fields", {}),
        expires_in=settings.presigned_url_expires_seconds,
        cloudfront_url=file_obj.cloudfront_url,
        status=file_obj.upload_status,
    )


def complete_upload(db: Session, file_id: str) -> File:
    """
    確認上傳完成。

    流程：
    1. 確認檔案紀錄存在
    2. 若狀態已是 uploaded，直接回傳
    3. 若狀態不是 pending，回傳 conflict
    4. 確認 S3 物件是否存在
    5. 讀取前 2KB，驗證 magic number
    6. 更新 DB 狀態為 uploaded

    如果 magic number 驗證失敗：
    - DB 狀態改為 failed
    - 刪除 S3 物件
    - 回傳錯誤
    """

    file_obj = get_file(db, file_id)

    if file_obj.upload_status == FileStatus.UPLOADED:
        return file_obj

    if file_obj.upload_status != FileStatus.PENDING:
        raise ConflictError(
            f"File status is {file_obj.upload_status}, expected pending."
        )

    exists = s3_service.object_exists(file_obj.s3_key)

    if not exists:
        file_obj.upload_status = FileStatus.FAILED
        db.commit()
        db.refresh(file_obj)

        raise UploadObjectNotFoundError("Uploaded object was not found in storage.")

    try:
        _validate_magic_numbers(file_obj)
    except AppError as exc:
        file_obj.upload_status = FileStatus.FAILED
        db.commit()
        db.refresh(file_obj)

        s3_service.delete_object(file_obj.s3_key)

        logger.warning(
            "File failed magic number validation: file_id=%s s3_key=%s reason=%s",
            file_obj.id,
            file_obj.s3_key,
            exc.message,
        )

        raise

    file_obj.upload_status = FileStatus.UPLOADED
    db.commit()
    db.refresh(file_obj)

    logger.info(
        "File upload completed: file_id=%s s3_key=%s",
        file_obj.id,
        file_obj.s3_key,
    )

    return file_obj
