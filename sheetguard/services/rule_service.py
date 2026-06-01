"""Rule library management service."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from sheetguard.core.rule_engine import RuleEngine
from sheetguard.models.rules import RuleSet
from sheetguard.utils.paths import rules_library_dir


class RuleService:
    """CRUD operations for rule sets in the local library."""

    def __init__(self, library_dir: Path | None = None) -> None:
        self.library_dir = library_dir or rules_library_dir()

    def _safe_filename(self, name: str) -> str:
        slug = re.sub(r"[^\w\-]+", "_", name.strip().lower())
        return slug or "rule_set"

    def library_path(self, rule_set: RuleSet) -> Path:
        return self.library_dir / f"{self._safe_filename(rule_set.rule_name)}.json"

    def save_to_library(self, rule_set: RuleSet) -> Path:
        path = self.library_path(rule_set)
        return RuleEngine.save(rule_set, path)

    def load_from_library(self, path: str | Path) -> RuleSet:
        return RuleEngine.load(path)

    def list_entries(self) -> list[dict[str, Any]]:
        entries = []
        for path in sorted(self.library_dir.glob("*.json")):
            try:
                rs = RuleEngine.load(path)
                entries.append(
                    {
                        "path": str(path),
                        "rule_name": rs.rule_name,
                        "description": rs.description,
                        "columns": len(rs.columns),
                    }
                )
            except Exception:
                continue
        return entries

    def delete(self, path: str | Path) -> None:
        Path(path).unlink(missing_ok=True)

    def import_file(self, path: str | Path) -> RuleSet:
        rs = RuleEngine.load(path)
        self.save_to_library(rs)
        return rs

    def export_file(self, rule_set: RuleSet, path: str | Path) -> Path:
        return RuleEngine.save(rule_set, path)

    def clone(self, rule_set: RuleSet, new_name: str) -> RuleSet:
        cloned = RuleEngine.clone(rule_set, new_name)
        self.save_to_library(cloned)
        return cloned
