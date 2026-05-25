"""Column letter/name resolution for rule definitions."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

_COLUMN_LETTER_RE = re.compile(r"^[A-Z]+$", re.IGNORECASE)


def column_letter_to_index(letter: str) -> int:
    """Convert Excel column letter (e.g. 'F') to zero-based index."""
    letter = letter.strip().upper()
    index = 0
    for char in letter:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index - 1


def resolve_column_name(df: pd.DataFrame, column: str) -> str:
    """
    Resolve a rule column reference to an actual DataFrame column name.

    Supports: Excel letters (A, F), header names, or numeric index strings.
    """
    column = str(column).strip()
    if column in df.columns:
        return column
    if _COLUMN_LETTER_RE.match(column):
        idx = column_letter_to_index(column)
        if 0 <= idx < len(df.columns):
            return str(df.columns[idx])
    if column.isdigit():
        idx = int(column)
        if 0 <= idx < len(df.columns):
            return str(df.columns[idx])
    raise KeyError(f"Column '{column}' not found in dataset ({len(df.columns)} columns)")


def series_for_field(df: pd.DataFrame, column: str) -> pd.Series:
    """Return the Series for a field column reference."""
    name = resolve_column_name(df, column)
    return df[name]


def coerce_cell(value: Any) -> Any:
    """Normalize pandas/numpy cell values for display and export."""
    if pd.isna(value):
        return ""
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, AttributeError):
            pass
    return value
