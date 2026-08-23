import os
from pathlib import Path

import pytest

from passage.config import AppConfig, prepare_private_root


def test_private_root_must_be_absolute(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="absolute"):
        AppConfig(private_root=Path("relative/private"))


def test_private_root_cannot_be_inside_repository(tmp_path: Path) -> None:
    config = AppConfig(private_root=tmp_path / "repo" / "private")

    with pytest.raises(ValueError, match="outside the repository"):
        config.validate_for_repository(tmp_path / "repo")


def test_private_root_rejects_symlink_components(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    config = AppConfig(private_root=link / "private")

    with pytest.raises(ValueError, match="symlink"):
        config.validate_for_repository(tmp_path / "repo")


def test_prepare_private_root_uses_restrictive_mode_despite_umask(tmp_path: Path) -> None:
    root = tmp_path / "private"
    config = AppConfig(private_root=root)
    old_umask = os.umask(0)
    try:
        prepare_private_root(config, tmp_path / "repo")
    finally:
        os.umask(old_umask)

    assert root.stat().st_mode & 0o777 == 0o700


def test_loopback_configuration_rejects_remote_bind(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="loopback"):
        AppConfig(private_root=tmp_path / "private", host="0.0.0.0")
