import base64

import pytest

from app.core.exceptions import UnsupportedContentTypeError
from app.services.filetype_service import filetype_service


# 1x1 transparent PNG
PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
    "AAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


@pytest.fixture
def png_bytes() -> bytes:
    return base64.b64decode(PNG_BASE64)


def test_valid_png(png_bytes: bytes):
    """
    PNG bytes + declared image/png，應該通過。
    """

    filetype_service.validate_magic_bytes(
        content=png_bytes,
        expected_content_type="image/png",
    )


def test_png_declared_as_jpeg_should_fail(png_bytes: bytes):
    """
    實際是 PNG，但宣告成 image/jpeg，應該失敗。
    """

    with pytest.raises(UnsupportedContentTypeError):
        filetype_service.validate_magic_bytes(
            content=png_bytes,
            expected_content_type="image/jpeg",
        )


def test_text_file_declared_as_png_should_fail():
    """
    純文字內容偽造為 image/png，應該失敗。
    """

    with pytest.raises(UnsupportedContentTypeError):
        filetype_service.validate_magic_bytes(
            content=b"This is not an image",
            expected_content_type="image/png",
        )


def test_empty_content_should_fail():
    """
    空內容無法驗證，應該失敗。
    """

    with pytest.raises(UnsupportedContentTypeError):
        filetype_service.validate_magic_bytes(
            content=b"",
            expected_content_type="image/png",
        )
