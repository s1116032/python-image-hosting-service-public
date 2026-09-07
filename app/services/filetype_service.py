import logging
from typing import Optional

import filetype

from app.core.config import get_settings
from app.core.exceptions import UnsupportedContentTypeError

settings = get_settings()
logger = logging.getLogger(__name__)


class FileTypeService:
    def guess_mime(self, content: bytes) -> Optional[str]:
        """
        使用 filetype 從檔案內容推測 MIME Type。

        通常只需要前幾百到前 2048 bytes。
        """

        if not content:
            return None

        kind = filetype.guess(content)

        if not kind:
            return None

        return kind.mime

    def validate_magic_bytes(
        self,
        content: bytes,
        expected_content_type: str,
    ) -> None:
        """
        驗證實際檔案內容的 MIME Type。

        規則：
        1. 必須能被 filetype 辨識
        2. 辨識出的 MIME Type 必須等於客户端宣告的 content_type
        3. 辨識出的 MIME Type 必須在白名單內
        """

        if not content:
            raise UnsupportedContentTypeError(
                "File content is empty; cannot validate magic numbers."
            )

        detected_mime = self.guess_mime(content)

        if detected_mime is None:
            raise UnsupportedContentTypeError(
                "Unable to detect MIME type from magic numbers."
            )

        normalized_detected = detected_mime.lower()
        normalized_expected = expected_content_type.lower()
        allowed_types = [item.lower() for item in settings.allowed_content_type_list]

        if normalized_detected != normalized_expected:
            raise UnsupportedContentTypeError(
                f"Declared content type {expected_content_type} "
                f"does not match detected MIME type {detected_mime}."
            )

        if normalized_detected not in allowed_types:
            raise UnsupportedContentTypeError(
                f"Detected MIME type {detected_mime} is not allowed."
            )

        logger.info(
            "Magic number validation passed: detected=%s expected=%s",
            detected_mime,
            expected_content_type,
        )


filetype_service = FileTypeService()
