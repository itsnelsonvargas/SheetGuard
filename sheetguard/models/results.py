"""Processing result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class ValidationIssue:
    """A single validation finding."""

    row_index: int
    field_id: str
    column: str
    severity: str  # error | warning
    message: str
    original_value: Any = ""
    cleaned_value: Any = ""
    rule_type: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "row": self.row_index + 1,
            "field_id": self.field_id,
            "column": self.column,
            "severity": self.severity,
            "message": self.message,
            "original_value": self.original_value,
            "cleaned_value": self.cleaned_value,
            "rule_type": self.rule_type,
        }


@dataclass
class DuplicateGroup:
    """Duplicate cluster for a given duplicate rule."""

    rule_name: str
    key_values: dict[str, Any]
    row_indices: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "key": self.key_values,
            "rows": [i + 1 for i in self.row_indices],
            "count": len(self.row_indices),
        }


@dataclass
class ProcessingResult:
    """Aggregated output from the processing pipeline."""

    cleaned_df: pd.DataFrame
    original_df: pd.DataFrame
    issues: list[ValidationIssue] = field(default_factory=list)
    duplicates: list[DuplicateGroup] = field(default_factory=list)
    corrections: dict[tuple[int, str], Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")
