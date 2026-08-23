from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any

from passage.domain.errors import InvalidQueryError
from passage.domain.models import LexicalMode, LexicalSearchRequest

_CURSOR_NAMESPACE = b"passage-cursor-v1\0"


@dataclass(frozen=True, slots=True)
class CursorPosition:
    raw_score: float
    canonical_order: int
    lane_priority: int = 0


def compile_fts_query(query: str, mode: LexicalMode, near_distance: int | None) -> str:
    if mode is LexicalMode.PHRASE:
        return _quote(query)
    terms = query.split()
    if not terms:
        raise InvalidQueryError("query must contain a searchable token")
    if mode is LexicalMode.TERMS:
        return " AND ".join(_quote(term) for term in terms)
    if mode is LexicalMode.PREFIX:
        return " AND ".join(f"{_quote(term)}*" for term in terms)
    distance = near_distance if near_distance is not None else 5
    return f"NEAR({' '.join(_quote(term) for term in terms)}, {distance})"


def request_fingerprint(request: LexicalSearchRequest | dict[str, Any]) -> str:
    if isinstance(request, LexicalSearchRequest):
        value = request.model_dump(mode="json", exclude={"cursor"})
    else:
        value = {key: item for key, item in request.items() if key != "cursor"}
    return hashlib.sha256(_json(value)).hexdigest()


def encode_cursor(fingerprint: str, position: CursorPosition) -> str:
    body = _json(
        {
            "fingerprint": fingerprint,
            "raw_score": position.raw_score,
            "canonical_order": position.canonical_order,
            "lane_priority": position.lane_priority,
        }
    )
    checksum = hashlib.sha256(_CURSOR_NAMESPACE + body).hexdigest()
    envelope = _json({"body": base64.urlsafe_b64encode(body).decode("ascii"), "checksum": checksum})
    return base64.urlsafe_b64encode(envelope).decode("ascii").rstrip("=")


def decode_cursor(cursor: str, expected_fingerprint: str) -> CursorPosition:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        envelope = json.loads(base64.urlsafe_b64decode(padded))
        body = base64.urlsafe_b64decode(envelope["body"])
        checksum = hashlib.sha256(_CURSOR_NAMESPACE + body).hexdigest()
        if not hmac.compare_digest(checksum, envelope["checksum"]):
            raise ValueError("checksum mismatch")
        value = json.loads(body)
        if value["fingerprint"] != expected_fingerprint:
            raise ValueError("request mismatch")
        return CursorPosition(
            raw_score=float(value["raw_score"]),
            canonical_order=int(value["canonical_order"]),
            lane_priority=int(value.get("lane_priority", 0)),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise InvalidQueryError("cursor does not match this pinned request") from exc


def _quote(value: str) -> str:
    return f'"{value.replace(chr(34), chr(34) * 2)}"'


def _json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
