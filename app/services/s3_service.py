import logging
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if settings.use_mock_aws:
            return None

        if self._client is None:
            self._client = boto3.client(
                "s3",
                region_name=settings.aws_region,
            )

        return self._client

    def build_cloudfront_url(self, s3_key: str) -> str:
        domain = settings.cloudfront_domain.strip().rstrip("/")

        if not domain:
            return f"https://mock-cloudfront.local/{s3_key}"

        if not domain.startswith("http"):
            domain = f"https://{domain}"

        return f"{domain}/{s3_key}"

    def generate_presigned_upload(
        self,
        *,
        s3_key: str,
        content_type: str,
        size_bytes: int,
        expires_in: int,
    ) -> Dict[str, Any]:
        """
        產生 S3 presigned upload 資訊。

        在 mock 模式下，不會真正呼叫 AWS。
        """

        if settings.use_mock_aws:
            return {
                "url": f"https://mock-s3.local/{settings.s3_bucket}/{s3_key}",
                "fields": {
                    "key": s3_key,
                    "Content-Type": content_type,
                    "X-Mock-Upload": "true",
                },
            }

        conditions = [
            {"Content-Type": content_type},
            ["content-length-range", 0, size_bytes],
        ]

        fields = {
            "Content-Type": content_type,
        }

        presigned = self.client.generate_presigned_post(
            Bucket=settings.s3_bucket,
            Key=s3_key,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=expires_in,
        )

        return presigned

    def object_exists(self, s3_key: str) -> bool:
        """
        確認 S3 物件是否存在。

        在 mock 模式下，直接回傳 True。
        """

        if settings.use_mock_aws:
            return True

        try:
            self.client.head_object(
                Bucket=settings.s3_bucket,
                Key=s3_key,
            )
            return True
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")

            if code in {"404", "NoSuchKey", "NotFound"}:
                return False

            logger.exception("Failed to check S3 object: %s", s3_key)
            raise

    def get_object_first_bytes(
        self,
        s3_key: str,
        byte_count: int,
    ) -> bytes:
        """
        讀取 S3 物件前 N bytes，用於 Magic Number 驗證。

        在 mock 模式下，回傳空 bytes。
        """

        if byte_count <= 0:
            return b""

        if settings.use_mock_aws:
            return b""

        try:
            response = self.client.get_object(
                Bucket=settings.s3_bucket,
                Key=s3_key,
                Range=f"bytes=0-{byte_count - 1}",
            )

            body = response.get("Body")

            if not body:
                return b""

            return body.read(byte_count)

        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")

            if code in {"404", "NoSuchKey", "NotFound"}:
                return b""

            logger.exception(
                "Failed to read first bytes from S3 object: %s",
                s3_key,
            )
            raise

    def delete_object(self, s3_key: str) -> None:
        """
        刪除 S3 物件。

        如果檔案未通過驗證，會呼叫這個方法清掉不合法上傳。
        """

        if settings.use_mock_aws:
            return

        try:
            self.client.delete_object(
                Bucket=settings.s3_bucket,
                Key=s3_key,
            )

            logger.info(
                "Deleted invalid S3 object: %s",
                s3_key,
            )

        except ClientError:
            logger.exception(
                "Failed to delete S3 object: %s",
                s3_key,
            )


s3_service = S3Service()