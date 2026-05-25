"""Deprecated package name — use ``sheetguard`` instead."""

from __future__ import annotations

import warnings

warnings.warn(
    "The masterlist_cleaner package was renamed to sheetguard.",
    DeprecationWarning,
    stacklevel=2,
)

from sheetguard import *  # noqa: F401,F403
