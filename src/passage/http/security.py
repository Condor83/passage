from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from urllib.parse import urlsplit

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from passage.config import AppConfig
from passage.domain.errors import ErrorCode
from passage.http.dependencies import error_response


@dataclass(frozen=True, slots=True)
class Authority:
    host: str
    port: int | None


@dataclass(frozen=True, slots=True)
class LocalSecurityPolicy:
    allowed_hosts: tuple[Authority, ...]
    allowed_origins: frozenset[str]

    @classmethod
    def from_config(cls, config: AppConfig) -> LocalSecurityPolicy:
        require_loopback_bind(config.host)
        if not config.allowed_hosts:
            raise ValueError("allowed_hosts must contain at least one loopback host")
        allowed_hosts = tuple(_parse_loopback_authority(value) for value in config.allowed_hosts)
        allowed_origins = frozenset(
            _normalize_local_origin(value) for value in config.allowed_origins
        )
        return cls(allowed_hosts=allowed_hosts, allowed_origins=allowed_origins)

    def permits_host(self, value: str) -> bool:
        try:
            candidate = _parse_loopback_authority(value)
        except ValueError:
            return False
        return any(
            candidate.host == allowed.host
            and (allowed.port is None or candidate.port == allowed.port)
            for allowed in self.allowed_hosts
        )

    def permits_origin(self, value: str) -> bool:
        try:
            normalized = _normalize_local_origin(value)
        except ValueError:
            return False
        return normalized in self.allowed_origins


class LocalRequestSecurityMiddleware:
    def __init__(self, app: ASGIApp, *, policy: LocalSecurityPolicy) -> None:
        self.app = app
        self.policy = policy

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = scope.get("headers", [])
        host_values = [
            value.decode("latin-1") for name, value in headers if name.lower() == b"host"
        ]
        if len(host_values) != 1 or not self.policy.permits_host(host_values[0]):
            response = error_response(
                status_code=400,
                code=ErrorCode.INVALID_QUERY,
                message="request host is not allowed",
            )
            await response(scope, receive, send)
            return

        origin_values = [
            value.decode("latin-1") for name, value in headers if name.lower() == b"origin"
        ]
        if len(origin_values) > 1 or (
            origin_values and not self.policy.permits_origin(origin_values[0])
        ):
            response = error_response(
                status_code=403,
                code=ErrorCode.INVALID_QUERY,
                message="request origin is not allowed",
            )
            await response(scope, receive, send)
            return

        async def send_with_security_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != b"x-content-type-options"
                ]
                response_headers.append((b"x-content-type-options", b"nosniff"))
                message["headers"] = response_headers
            await send(message)

        await self.app(scope, receive, send_with_security_headers)


def require_loopback_bind(host: str) -> None:
    normalized = host.strip().lower()
    if normalized == "localhost":
        return
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError as exc:
        raise ValueError("HTTP bind host must be a loopback address or localhost") from exc
    if not address.is_loopback:
        raise ValueError("HTTP bind host must be loopback")


def _parse_loopback_authority(value: str) -> Authority:
    if not value or value != value.strip() or any(character in value for character in "/?#@,"):
        raise ValueError("host must be a loopback authority")

    if value.startswith("["):
        closing = value.find("]")
        if closing < 0:
            raise ValueError("invalid bracketed host")
        raw_host = value[1:closing]
        remainder = value[closing + 1 :]
        if remainder and not remainder.startswith(":"):
            raise ValueError("invalid bracketed host")
        raw_port = remainder[1:] if remainder else None
    else:
        if value.count(":") > 1:
            raise ValueError("IPv6 host authorities must be bracketed")
        raw_host, separator, raw_port_value = value.partition(":")
        raw_port = raw_port_value if separator else None

    port = _parse_port(raw_port)
    normalized_host = raw_host.lower()
    if normalized_host == "localhost":
        return Authority(normalized_host, port)
    try:
        address = ipaddress.ip_address(normalized_host)
    except ValueError as exc:
        raise ValueError("host must be localhost or a loopback address") from exc
    if not address.is_loopback:
        raise ValueError("host must be loopback")
    return Authority(address.compressed, port)


def _parse_port(value: str | None) -> int | None:
    if value is None:
        return None
    if not value or not value.isascii() or not value.isdecimal():
        raise ValueError("host port must be a decimal integer")
    port = int(value)
    if not 1 <= port <= 65535:
        raise ValueError("host port is outside the supported range")
    return port


def _normalize_local_origin(value: str) -> str:
    if not value or value != value.strip():
        raise ValueError("origin must be an absolute local origin")
    parsed = urlsplit(value)
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("origin must contain only scheme and local authority")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("origin port is invalid") from exc
    host = parsed.hostname
    if host is None:
        raise ValueError("origin host is missing")
    if ":" in host:
        host_authority = f"[{host}]:{port}" if port is not None else f"[{host}]"
    else:
        host_authority = f"{host}:{port}" if port is not None else host
    authority = _parse_loopback_authority(host_authority)
    rendered_host = f"[{authority.host}]" if ":" in authority.host else authority.host
    rendered_port = f":{authority.port}" if authority.port is not None else ""
    return f"{parsed.scheme.lower()}://{rendered_host}{rendered_port}"
