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

    def drop_row(self, row_index: int) -> None:
        """Surgically remove a row and update all related metadata indices."""
        # 1. Update DataFrames
        self.cleaned_df = self.cleaned_df.drop(self.cleaned_df.index[row_index]).reset_index(drop=True)
        self.original_df = self.original_df.drop(self.original_df.index[row_index]).reset_index(drop=True)

        # 2. Update Issues
        new_issues = []
        for issue in self.issues:
            if issue.row_index == row_index:
                continue
            if issue.row_index > row_index:
                issue.row_index -= 1
            new_issues.append(issue)
        self.issues = new_issues

        # 3. Update Duplicates
        new_duplicates = []
        for group in self.duplicates:
            new_indices = []
            for idx in group.row_indices:
                if idx == row_index:
                    continue
                if idx > row_index:
                    new_indices.append(idx - 1)
                else:
                    new_indices.append(idx)
            
            if len(new_indices) >= 2:
                group.row_indices = new_indices
                new_duplicates.append(group)
        self.duplicates = new_duplicates

        # 4. Update Corrections
        new_corrections = {}
        for (idx, col), val in self.corrections.items():
            if idx == row_index:
                continue
            if idx > row_index:
                new_corrections[(idx - 1, col)] = val
            else:
                new_corrections[(idx, col)] = val
        self.corrections = new_corrections

        # 5. Update Summary
        if self.summary:
            self.summary["total_rows"] = len(self.cleaned_df)
