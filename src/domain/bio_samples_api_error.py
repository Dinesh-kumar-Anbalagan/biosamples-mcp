from typing import Any

class BioSamplesAPIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        details: list[dict[str, Any]] | None = None,
        retryable: bool = True,):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or []
        self.retryable = retryable