"""Application error hierarchy. Every error becomes a JSON envelope via main.py handlers."""


class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str, *, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details


class BadRequestError(AppError):
    status_code = 400
    code = "bad_request"


class InvalidImageError(AppError):
    status_code = 400
    code = "invalid_image"


class UnsupportedFormatError(AppError):
    status_code = 415
    code = "unsupported_format"


class ImageTooLargeError(AppError):
    status_code = 413
    code = "image_too_large"


class MissingAPIKeyError(AppError):
    status_code = 500
    code = "missing_api_key"


class ProviderError(AppError):
    """Non-transient provider failure (bad request, auth, empty response)."""

    status_code = 502
    code = "provider_error"


class ProviderUnavailableError(AppError):
    """Transient provider failure (5xx, connection issues) — safe to retry."""

    status_code = 503
    code = "provider_unavailable"


class ProviderTimeoutError(AppError):
    status_code = 504
    code = "provider_timeout"


class RateLimitError(AppError):
    status_code = 429
    code = "rate_limited"


class MalformedAIResponseError(AppError):
    status_code = 502
    code = "malformed_ai_response"
