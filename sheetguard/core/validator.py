"""Validation engine with pluggable rule types."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from rapidfuzz import fuzz, process

from sheetguard.models.results import ValidationIssue
from sheetguard.models.rules import ColumnRule, LookupSource, RuleSet
from sheetguard.utils.column_utils import resolve_column_name

logger = logging.getLogger(__name__)


class DataValidator:
    """Validate cleaned data against rule set constraints."""

    def __init__(self, rule_set: RuleSet, lookup_cache: dict[str, set[str]] | None = None) -> None:
        self.rule_set = rule_set
        self._lookup_cache = lookup_cache or {}
        self._issues: list[ValidationIssue] = []

    @property
    def issues(self) -> list[ValidationIssue]:
        return self._issues

    def load_lookups(self) -> dict[str, set[str]]:
        """Load all configured lookup sources into memory."""
        cache: dict[str, set[str]] = {}
        for src in self.rule_set.lookups:
            cache[src.name] = self._load_lookup_keys(src)
            logger.info("Loaded lookup '%s' with %d keys", src.name, len(cache[src.name]))
        self._lookup_cache = cache
        return cache

    def validate(self, df: pd.DataFrame, original_df: pd.DataFrame | None = None) -> list[ValidationIssue]:
        """Run all column validations and return issues."""
        self._issues = []
        if not self._lookup_cache and self.rule_set.lookups:
            self.load_lookups()

        orig = original_df if original_df is not None else df

        for col_rule in self.rule_set.columns:
            col_name = resolve_column_name(df, col_rule.column)
            series = df[col_name]
            orig_series = resolve_column_name(orig, col_rule.column)
            orig_series = orig[orig_series]

            self._check_required(col_rule, col_name, series)
            self._check_allowed(col_rule, col_name, series)
            self._check_regex(col_rule, col_name, series)
            self._check_length(col_rule, col_name, series)
            self._check_numeric_range(col_rule, col_name, series)
            self._check_date(col_rule, col_name, series)
            self._check_email(col_rule, col_name, series)
            self._check_lookup(col_rule, col_name, series)

        logger.info("Validation found %d issues", len(self._issues))
        return self._issues

    def _add(
        self,
        row: int,
        col_rule: ColumnRule,
        col_name: str,
        severity: str,
        message: str,
        original: Any,
        cleaned: Any,
        rule_type: str,
    ) -> None:
        self._issues.append(
            ValidationIssue(
                row_index=row,
                field_id=col_rule.field_id,
                column=col_name,
                severity=severity,
                message=message,
                original_value=original,
                cleaned_value=cleaned,
                rule_type=rule_type,
            )
        )

    def _severity(self, col_rule: ColumnRule) -> str:
        return "warning" if col_rule.warning_only else "error"

    def _check_required(self, col_rule: ColumnRule, col_name: str, series: pd.Series) -> None:
        if not col_rule.required:
            return
        empty = series.isna() | (series.astype(str).str.strip() == "")
        for idx in empty[empty].index:
            self._add(
                int(idx),
                col_rule,
                col_name,
                self._severity(col_rule),
                "Required field is empty",
                "",
                series.loc[idx],
                "required",
            )

    def _check_allowed(self, col_rule: ColumnRule, col_name: str, series: pd.Series) -> None:
        if not col_rule.allowed_values:
            return
        allowed = {str(v).strip().upper() for v in col_rule.allowed_values}
        for idx, val in series.items():
            if pd.isna(val) or str(val).strip() == "":
                continue
            if str(val).strip().upper() not in allowed:
                self._add(
                    int(idx),
                    col_rule,
                    col_name,
                    self._severity(col_rule),
                    f"Value not in allowed list: {col_rule.allowed_values}",
                    val,
                    val,
                    "allowed_values",
                )

    def _check_regex(self, col_rule: ColumnRule, col_name: str, series: pd.Series) -> None:
        if not col_rule.regex:
            return
        pattern = re.compile(col_rule.regex)
        for idx, val in series.items():
            if pd.isna(val) or str(val).strip() == "":
                continue
            if not pattern.match(str(val).strip()):
                self._add(
                    int(idx),
                    col_rule,
                    col_name,
                    self._severity(col_rule),
                    f"Value does not match pattern: {col_rule.regex}",
                    val,
                    val,
                    "regex",
                )

    def _check_length(self, col_rule: ColumnRule, col_name: str, series: pd.Series) -> None:
        for idx, val in series.items():
            if pd.isna(val):
                continue
            s = str(val).strip()
            if col_rule.min_length is not None and len(s) < col_rule.min_length:
                self._add(
                    int(idx),
                    col_rule,
                    col_name,
                    self._severity(col_rule),
                    f"Length {len(s)} below minimum {col_rule.min_length}",
                    val,
                    val,
                    "min_length",
                )
            if col_rule.max_length is not None and len(s) > col_rule.max_length:
                self._add(
                    int(idx),
                    col_rule,
                    col_name,
                    self._severity(col_rule),
                    f"Length {len(s)} exceeds maximum {col_rule.max_length}",
                    val,
                    val,
                    "max_length",
                )

    def _check_numeric_range(self, col_rule: ColumnRule, col_name: str, series: pd.Series) -> None:
        if col_rule.min_value is None and col_rule.max_value is None:
            return
        for idx, val in series.items():
            if pd.isna(val) or str(val).strip() == "":
                continue
            try:
                num = float(str(val).replace(",", ""))
            except ValueError:
                self._add(
                    int(idx),
                    col_rule,
                    col_name,
                    self._severity(col_rule),
                    "Value is not numeric",
                    val,
                    val,
                    "numeric_range",
                )
                continue
            if col_rule.min_value is not None and num < col_rule.min_value:
                self._add(
                    int(idx),
                    col_rule,
                    col_name,
                    self._severity(col_rule),
                    f"Value {num} below minimum {col_rule.min_value}",
                    val,
                    val,
                    "numeric_range",
                )
            if col_rule.max_value is not None and num > col_rule.max_value:
                self._add(
                    int(idx),
                    col_rule,
                    col_name,
                    self._severity(col_rule),
                    f"Value {num} above maximum {col_rule.max_value}",
                    val,
                    val,
                    "numeric_range",
                )

    def _check_date(self, col_rule: ColumnRule, col_name: str, series: pd.Series) -> None:
        if not col_rule.date_format:
            return
        fmt = col_rule.date_format.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
        for idx, val in series.items():
            if pd.isna(val) or str(val).strip() == "":
                continue
            s = str(val).strip()
            try:
                datetime.strptime(s, fmt)
            except ValueError:
                parsed = pd.to_datetime(s, errors="coerce", dayfirst=True)
                if pd.isna(parsed):
                    self._add(
                        int(idx),
                        col_rule,
                        col_name,
                        self._severity(col_rule),
                        f"Invalid date (expected format {col_rule.date_format})",
                        val,
                        val,
                        "date",
                    )

    def _check_email(self, col_rule: ColumnRule, col_name: str, series: pd.Series) -> None:
        if not col_rule.validate_email:
            return
        # Basic email regex
        pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        for idx, val in series.items():
            if pd.isna(val) or str(val).strip() == "":
                continue
            s = str(val).strip()
            if not pattern.match(s):
                self._add(
                    int(idx),
                    col_rule,
                    col_name,
                    self._severity(col_rule),
                    f"Invalid email address: {s}",
                    val,
                    val,
                    "email",
                )

    def _check_lookup(self, col_rule: ColumnRule, col_name: str, series: pd.Series) -> None:
        if not col_rule.lookup:
            return
        keys = self._lookup_cache.get(col_rule.lookup)
        if keys is None:
            logger.warning("Lookup '%s' not loaded", col_rule.lookup)
            return
        src = next((l for l in self.rule_set.lookups if l.name == col_rule.lookup), None)
        threshold = src.fuzzy_threshold if src else 90.0

        for idx, val in series.items():
            if pd.isna(val) or str(val).strip() == "":
                continue
            s = str(val).strip().upper()
            if s in keys:
                continue
            match = process.extractOne(
                s,
                list(keys),
                scorer=fuzz.ratio,
                score_cutoff=threshold,
            )
            if match is None:
                self._add(
                    int(idx),
                    col_rule,
                    col_name,
                    self._severity(col_rule),
                    f"Value not found in lookup '{col_rule.lookup}'",
                    val,
                    val,
                    "lookup",
                )

    @staticmethod
    def _load_lookup_keys(src: LookupSource) -> set[str]:
        from sheetguard.utils.paths import app_root

        path = Path(src.path)
        if not path.is_absolute():
            path = app_root() / path
        if not path.exists():
            logger.error("Lookup file not found: %s", path)
            return set()

        if path.suffix.lower() in {".xlsx", ".xls"}:
            df = pd.read_excel(path, sheet_name=src.sheet or 0)
        else:
            df = pd.read_csv(path)

        if src.key_column not in df.columns:
            idx = 0
            try:
                from sheetguard.utils.column_utils import column_letter_to_index

                idx = column_letter_to_index(src.key_column)
            except Exception:
                pass
            col = df.columns[idx]
        else:
            col = src.key_column

        return {str(v).strip().upper() for v in df[col].dropna().unique()}
