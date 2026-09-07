class AppError(Exception):
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "Internal server error"

    def __init__(self, message: str | None = None):
        if message:
            self.message = message
        super().__init__(self.message)


class ResourceNotFoundError(AppError):
    status_code = 404
    error_code = "RESOURCE_NOT_FOUND"
    message = "Resource not found"


class UnsupportedContentTypeError(AppError):
    status_code = 400
    error_code = "UNSUPPORTED_CONTENT_TYPE"
    message = "Unsupported content type"


class FileTooLargeError(AppError):
    status_code = 400
    error_code = "FILE_TOO_LARGE"
    message = "File size exceeds allowed limit"


class ConflictError(AppError):
    status_code = 409
    error_code = "CONFLICT"
    message = "Resource state conflict"


class UploadObjectNotFoundError(AppError):
    status_code = 409
    error_code = "UPLOAD_OBJECT_NOT_FOUND"
    message = "Uploaded object was not found in storage"
