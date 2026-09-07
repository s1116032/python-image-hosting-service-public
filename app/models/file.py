import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class FileStatus:
    PENDING = "pending"
    UPLOADED = "uploaded"
    FAILED = "failed"


def generate_uuid() -> str:
    return str(uuid.uuid4())


class File(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    s3_key: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        unique=True,
        index=True,
    )

    content_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    upload_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=FileStatus.PENDING,
        index=True,
    )

    cloudfront_url: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )

    created_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
