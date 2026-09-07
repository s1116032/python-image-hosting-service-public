from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "local"

    database_url: str = "sqlite:///./image_hosting.db"

    aws_region: str = "us-east-2"
    s3_bucket: str = "local-image-hosting-bucket"
    cloudfront_domain: str = "mock-cloudfront.local"

    presigned_url_expires_seconds: int = 300
    max_file_size_mb: int = 10
    allowed_content_types: str = "image/jpeg,image/png,image/webp,image/gif"

    use_mock_aws: bool = True

    validate_magic_bytes: bool = True
    magic_bytes_limit: int = 2048

    log_level: str = "INFO"

    @property
    def allowed_content_type_list(self) -> List[str]:
        return [
            item.strip()
            for item in self.allowed_content_types.split(",")
            if item.strip()
        ]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
