"""Filesystem locations shared by source checkouts and installed packages."""

from __future__ import annotations

import os
import shutil
import sys
import sysconfig
from pathlib import Path


def _user_data_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Avatar"
    if os.name == "nt":
        base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "Avatar"
    base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "avatar"


def _seed_builtin_assets(source: Path, target: Path) -> None:
    """Copy packaged read-only assets into a writable data directory once."""
    if not source.exists() or source.resolve() == target.resolve():
        return

    target.mkdir(parents=True, exist_ok=True)
    for filename in ("README.md", "provenance.json"):
        source_file = source / filename
        target_file = target / filename
        if source_file.exists() and not target_file.exists():
            shutil.copy2(source_file, target_file)

    for dirname in ("profiles", "arcs", "logic"):
        source_dir = source / dirname
        if not source_dir.exists():
            continue
        target_dir = target / dirname
        target_dir.mkdir(parents=True, exist_ok=True)
        for source_file in source_dir.glob("*.json"):
            target_file = target_dir / source_file.name
            if not target_file.exists():
                shutil.copy2(source_file, target_file)


def resolve_data_dir() -> Path:
    """Resolve Avatar's visible, configurable data directory."""
    source_data = Path(__file__).resolve().parent.parent / "data"
    installed_data = (
        Path(sysconfig.get_path("data")) / "share" / "avatar" / "data"
    )

    configured = os.getenv("AVATAR_DATA_DIR")
    if configured:
        target = Path(configured).expanduser().resolve()
        seed_source = source_data if source_data.exists() else installed_data
        _seed_builtin_assets(seed_source, target)
        return target

    if source_data.exists():
        return source_data

    if installed_data.exists():
        target = _user_data_dir()
        _seed_builtin_assets(installed_data, target)
        return target

    return _user_data_dir()


DATA_DIR = resolve_data_dir()
