"""Application path resolution (PyInstaller-safe)."""

from __future__ import annotations

import sys
from pathlib import Path


def app_root() -> Path:
    """Return the application root directory."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[2]


def resource_path(*parts: str) -> Path:
    """Resolve a path under bundled resources."""
    base = app_root()
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return base.joinpath(*parts)


def rules_library_dir() -> Path:
    """Default directory for saved rule sets."""
    lib = app_root() / "data" / "rules_library"
    lib.mkdir(parents=True, exist_ok=True)
    return lib


def logs_dir() -> Path:
    """Directory for log files."""
    d = app_root() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d
