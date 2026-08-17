from __future__ import annotations

import ipaddress
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    private_root: Path
    host: str = "127.0.0.1"
    port: int = Field(default=8765, ge=1, le=65535)
    allowed_hosts: tuple[str, ...] = ("127.0.0.1", "localhost", "[::1]")
    allowed_origins: tuple[str, ...] = (
        "http://127.0.0.1",
        "http://localhost",
        "http://[::1]",
    )

    @field_validator("private_root")
    @classmethod
    def require_absolute_root(cls, root: Path) -> Path:
        if not root.is_absolute():
            raise ValueError("private_root must be absolute")
        return root

    @field_validator("host")
    @classmethod
    def require_loopback_host(cls, host: str) -> str:
        normalized = host.strip().lower()
        if normalized == "localhost":
            return normalized
        try:
            address = ipaddress.ip_address(normalized)
        except ValueError as exc:
            raise ValueError("host must be a loopback address or localhost") from exc
        if not address.is_loopback:
            raise ValueError("host must be loopback")
        return normalized

    def validate_for_repository(self, repository_root: Path) -> None:
        repository_root = repository_root.absolute()
        _reject_symlink_components(self.private_root)
        candidate = self.private_root.absolute()
        if candidate == repository_root or candidate.is_relative_to(repository_root):
            raise ValueError("private_root must be outside the repository")


def prepare_private_root(config: AppConfig, repository_root: Path) -> Path:
    config.validate_for_repository(repository_root)
    config.private_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    _reject_symlink_components(config.private_root)
    os.chmod(config.private_root, 0o700, follow_symlinks=False)
    return config.private_root


def create_private_file(path: Path, data: bytes = b"") -> None:
    _reject_symlink_components(path.parent)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _reject_symlink_components(path: Path) -> None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if current.is_symlink():
            raise ValueError(f"private path contains symlink component: {current}")
