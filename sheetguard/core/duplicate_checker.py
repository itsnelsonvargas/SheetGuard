"""Configurable duplicate detection."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from sheetguard.models.results import DuplicateGroup
from sheetguard.models.rules import DuplicateRule, RuleSet
from sheetguard.utils.column_utils import resolve_column_name

logger = logging.getLogger(__name__)


class DuplicateChecker:
    """Detect duplicate rows using composite key rules."""

    def __init__(self, rule_set: RuleSet) -> None:
        self.rule_set = rule_set

    def find_duplicates(self, df: pd.DataFrame) -> list[DuplicateGroup]:
        """Return all duplicate groups across configured rules."""
        groups: list[DuplicateGroup] = []
        for dup_rule in self.rule_set.duplicate_rules:
            groups.extend(self._check_rule(df, dup_rule))
        logger.info("Found %d duplicate groups", len(groups))
        return groups

    def _check_rule(self, df: pd.DataFrame, dup_rule: DuplicateRule) -> list[DuplicateGroup]:
        col_map: dict[str, str] = {}
        for field in dup_rule.fields:
            col_rule = next((c for c in self.rule_set.columns if c.field_id == field), None)
            if col_rule:
                col_map[field] = resolve_column_name(df, col_rule.column)
            else:
                col_map[field] = resolve_column_name(df, field)

        subset_cols = list(col_map.values())
        work = df[subset_cols].copy()
        for c in subset_cols:
            work[c] = work[c].astype(str).str.strip().str.upper()

        if dup_rule.match_mode == "fuzzy":
            return self._check_fuzzy(df, work, dup_rule)

        dup_mask = work.duplicated(keep=False)
        if not dup_mask.any():
            return []

        dup_df = df.loc[dup_mask]
        key_cols = subset_cols
        grouped: list[DuplicateGroup] = []

        for key_vals, group in dup_df.groupby(key_cols, dropna=False):
            indices = group.index.tolist()
            if len(indices) < 2:
                continue
            key_dict: dict[str, Any] = {}
            if isinstance(key_vals, tuple):
                for i, field in enumerate(dup_rule.fields):
                    key_dict[field] = key_vals[i] if i < len(key_vals) else ""
            else:
                key_dict[dup_rule.fields[0]] = key_vals
            grouped.append(
                DuplicateGroup(
                    rule_name=dup_rule.name,
                    key_values=key_dict,
                    row_indices=[int(i) for i in indices],
                )
            )
        return grouped

    def _check_fuzzy(self, df: pd.DataFrame, work: pd.DataFrame, dup_rule: DuplicateRule) -> list[DuplicateGroup]:
        """Detect duplicates using fuzzy matching on concatenated keys."""
        try:
            from rapidfuzz import fuzz, process
        except ImportError:
            logger.warning("rapidfuzz not installed, falling back to exact matching")
            dup_rule.match_mode = "exact"
            return self._check_rule(df, dup_rule)

        # Create a single string key for each row
        keys = work.apply(lambda r: " | ".join(r.values), axis=1).tolist()
        indices = work.index.tolist()
        
        visited = set()
        groups: list[DuplicateGroup] = []
        
        threshold = dup_rule.fuzzy_threshold

        for i in range(len(keys)):
            if i in visited:
                continue
            
            # Find similar keys
            current_key = keys[i]
            matches = process.extract(
                current_key, 
                keys[i+1:], 
                scorer=fuzz.token_sort_ratio, 
                score_cutoff=threshold
            )
            
            if matches:
                group_indices = [indices[i]]
                visited.add(i)
                
                for _, score, idx_in_subset in matches:
                    actual_idx = i + 1 + idx_in_subset
                    if actual_idx not in visited:
                        group_indices.append(indices[actual_idx])
                        visited.add(actual_idx)
                
                if len(group_indices) > 1:
                    # Representative key values
                    row_data = df.loc[group_indices[0]]
                    key_dict = {}
                    for field in dup_rule.fields:
                        col = next((c.column for c in self.rule_set.columns if c.field_id == field), field)
                        actual_col = resolve_column_name(df, col)
                        key_dict[field] = str(row_data.get(actual_col, ""))

                    groups.append(
                        DuplicateGroup(
                            rule_name=f"{dup_rule.name} (Fuzzy)",
                            key_values=key_dict,
                            row_indices=[int(idx) for idx in group_indices],
                        )
                    )
                    
        return groups

    def duplicates_dataframe(self, df: pd.DataFrame, groups: list[DuplicateGroup]) -> pd.DataFrame:
        """Build a report DataFrame listing duplicate rows."""
        rows: list[dict[str, Any]] = []
        for g in groups:
            for row_idx in g.row_indices:
                row_data = df.iloc[row_idx].to_dict()
                row_data["_duplicate_rule"] = g.rule_name
                row_data["_row_number"] = row_idx + 1
                row_data["_key"] = str(g.key_values)
                rows.append(row_data)
        if not rows:
            return pd.DataFrame(columns=["_duplicate_rule", "_row_number", "_key"])
        return pd.DataFrame(rows)
