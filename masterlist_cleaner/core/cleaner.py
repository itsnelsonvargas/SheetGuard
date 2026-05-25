"""Vectorized data cleaning operations."""

from __future__ import annotations

import logging
import re
from typing import Any

import pandas as pd

from sheetguard.models.rules import ColumnRule, RuleSet
from sheetguard.utils.column_utils import resolve_column_name

logger = logging.getLogger(__name__)

_SPECIAL_RE = re.compile(r"[^\w\s\-\.\@]", re.UNICODE)
_MULTI_SPACE_RE = re.compile(r"\s+")


class DataCleaner:
    """Apply configured cleaning transforms to a DataFrame."""

    def __init__(self, rule_set: RuleSet) -> None:
        self.rule_set = rule_set
        self._corrections: dict[tuple[int, str], Any] = {}

    @property
    def corrections(self) -> dict[tuple[int, str], Any]:
        return self._corrections

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a cleaned copy of the input DataFrame."""
        result = df.copy()
        for col_rule in self.rule_set.columns:
            if not col_rule.cleaning:
                continue
            col_name = resolve_column_name(result, col_rule.column)
            series = result[col_name].astype(object)
            cleaned = self._apply_cleaning(series, col_rule.cleaning)
            for idx, (old, new) in enumerate(zip(series.tolist(), cleaned.tolist())):
                if self._changed(old, new):
                    self._corrections[(idx, col_name)] = new
            result[col_name] = cleaned
        logger.info("Cleaning complete; %d cell corrections", len(self._corrections))
        return result

    def _apply_cleaning(self, series: pd.Series, ops: list[str]) -> pd.Series:
        out = series.copy()
        for op in ops:
            if op == "trim":
                out = out.map(self._trim)
            elif op == "collapse_spaces":
                out = out.map(self._collapse_spaces)
            elif op == "uppercase":
                out = out.map(self._upper)
            elif op == "lowercase":
                out = out.map(self._lower)
            elif op == "title":
                out = out.map(self._title)
            elif op == "remove_special":
                out = out.map(self._remove_special)
            elif op == "normalize_date":
                out = self._normalize_dates(out)
            elif op == "numeric_cleanup":
                out = out.map(self._numeric_cleanup)
            else:
                logger.warning("Unknown cleaning op skipped: %s", op)
        return out

    @staticmethod
    def _is_empty(val: Any) -> bool:
        return val is None or (isinstance(val, float) and pd.isna(val)) or (
            isinstance(val, str) and not str(val).strip()
        )

    @staticmethod
    def _changed(old: Any, new: Any) -> bool:
        if DataCleaner._is_empty(old) and DataCleaner._is_empty(new):
            return False
        return str(old) != str(new)

    @staticmethod
    def _trim(val: Any) -> Any:
        if DataCleaner._is_empty(val):
            return val
        return str(val).strip()

    @staticmethod
    def _collapse_spaces(val: Any) -> Any:
        if DataCleaner._is_empty(val):
            return val
        return _MULTI_SPACE_RE.sub(" ", str(val).strip())

    @staticmethod
    def _upper(val: Any) -> Any:
        if DataCleaner._is_empty(val):
            return val
        return str(val).upper()

    @staticmethod
    def _lower(val: Any) -> Any:
        if DataCleaner._is_empty(val):
            return val
        return str(val).lower()

    @staticmethod
    def _title(val: Any) -> Any:
        if DataCleaner._is_empty(val):
            return val
        return str(val).title()

    @staticmethod
    def _remove_special(val: Any) -> Any:
        if DataCleaner._is_empty(val):
            return val
        return _SPECIAL_RE.sub("", str(val)).strip()

    @staticmethod
    def _numeric_cleanup(val: Any) -> Any:
        if DataCleaner._is_empty(val):
            return val
        s = str(val).strip().replace(",", "")
        try:
            num = float(s)
            if num == int(num):
                return int(num)
            return num
        except ValueError:
            cleaned = re.sub(r"[^\d\.\-]", "", s)
            if not cleaned:
                return val
            try:
                num = float(cleaned)
                return int(num) if num == int(num) else num
            except ValueError:
                return val

    @staticmethod
    def _normalize_dates(series: pd.Series) -> pd.Series:
        parsed = pd.to_datetime(series, errors="coerce", dayfirst=True)
        result = series.copy()
        for i, dt in enumerate(parsed):
            if pd.notna(dt):
                result.iloc[i] = dt.strftime("%Y-%m-%d")
        return result
