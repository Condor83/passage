from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    INVALID_REFERENCE = "invalid_reference"
    INVALID_QUERY = "invalid_query"
    LIMIT_EXCEEDED = "limit_exceeded"
    PASSAGE_NOT_FOUND = "passage_not_found"
    VERSION_UNAVAILABLE = "version_unavailable"
    CORPUS_UNAVAILABLE = "corpus_unavailable"
    CONFIG_UNAVAILABLE = "config_unavailable"
    INTERNAL_ERROR = "internal_error"


@dataclass(slots=True)
class ScriptureChatError(Exception):
    code: ErrorCode
    message: str
    detail: dict[str, Any] | None = None

    def __str__(self) -> str:
        return self.message


class InvalidReferenceError(ScriptureChatError):
    def __init__(self, message: str, detail: dict[str, Any] | None = None) -> None:
        super().__init__(ErrorCode.INVALID_REFERENCE, message, detail)


class InvalidQueryError(ScriptureChatError):
    def __init__(self, message: str, detail: dict[str, Any] | None = None) -> None:
        super().__init__(ErrorCode.INVALID_QUERY, message, detail)


class LimitExceededError(ScriptureChatError):
    def __init__(self, message: str, detail: dict[str, Any] | None = None) -> None:
        super().__init__(ErrorCode.LIMIT_EXCEEDED, message, detail)


class PassageNotFoundError(ScriptureChatError):
    def __init__(self, reference: str) -> None:
        super().__init__(
            ErrorCode.PASSAGE_NOT_FOUND,
            "passage not found",
            {"reference": reference},
        )


class VersionUnavailableError(ScriptureChatError):
    def __init__(self, corpus_version: str) -> None:
        super().__init__(
            ErrorCode.VERSION_UNAVAILABLE,
            "corpus version is unavailable",
            {"corpus_version": corpus_version},
        )


class CorpusUnavailableError(ScriptureChatError):
    def __init__(self, message: str = "no usable corpus is active") -> None:
        super().__init__(ErrorCode.CORPUS_UNAVAILABLE, message)


class ConfigUnavailableError(ScriptureChatError):
    def __init__(self, message: str = "retrieval configuration is unavailable") -> None:
        super().__init__(ErrorCode.CONFIG_UNAVAILABLE, message)
