#!/usr/bin/env python3
"""One-time migration: masterlist_cleaner package -> sheetguard."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "masterlist_cleaner"
DST = ROOT / "sheetguard"

if SRC.exists():
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST)
    shutil.rmtree(SRC)
    print(f"Migrated {SRC.name} -> {DST.name}")
else:
    print(f"Source not found (already migrated?): {SRC}")

# Legacy shim only
shim = ROOT / "masterlist_cleaner" / "__init__.py"
if not shim.exists():
    shim.parent.mkdir(exist_ok=True)
    shim.write_text(
        '"""Deprecated — use sheetguard."""\n'
        "from sheetguard import *  # noqa: F401,F403\n",
        encoding="utf-8",
    )
