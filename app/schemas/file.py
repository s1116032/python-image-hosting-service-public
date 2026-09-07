from datetime import datetime
from typing import Dict

from pydantic import BaseModel, ConfigDict, Field


class FileUploadUrlCreate(BaseModel):
    filename: str = Field(
        min_length=1,
        max_length=255,
        examples=["demo.png"],
    )

    content_type: str = Field(
        min_length=1,
        max_length=255,
        examples=["image/png"],
    )

    size_bytes: int = Field(
        gt=0,
        examples=[102400],
    )


class FileUploadUrlResponse(BaseModel):
    file_id: str
    original_filename: str
    s3_key: str
    upload_url: str
    upload_fields: Dict[str, str]
    expires_in: int
    cloudfront_url: str
    status: str


class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file_id: str
    original_filename: str
    s3_key: str
    content_type: str
    size_bytes: int
    status: str
    cloudfront_url: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, file_obj) -> "FileResponse":
        return cls(
            file_id=file_obj.id,
            original_filename=file_obj.original_filename,
            s3_key=file_obj.s3_key,
            content_type=file_obj.content_type,
            size_bytes=file_obj.size_bytes,
            status=file_obj.upload_status,
            cloudfront_url=file_obj.cloudfront_url,
            created_at=file_obj.created_at,
            updated_at=file_obj.updated_at,
        )


class FileCompleteResponse(BaseModel):
    file_id: str
    status: str
    cloudfront_url: str
    updated_at: datetime

    @classmethod
    def from_model(cls, file_obj) -> "FileCompleteResponse":
        return cls(
            file_id=file_obj.id,
            status=file_obj.upload_status,
            cloudfront_url=file_obj.cloudfront_url,
            updated_at=file_obj.updated_at,
        )
