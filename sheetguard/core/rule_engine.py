"""JSON rule loading, validation, and persistence."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from sheetguard.models.rules import RuleSet
from sheetguard.utils.paths import rules_library_dir

logger = logging.getLogger(__name__)


class RuleEngine:
    """Load, save, clone, and validate rule set JSON files."""

    SUPPORTED_CLEANING = {
        "trim",
        "collapse_spaces",
        "uppercase",
        "lowercase",
        "title",
        "pascal_case",
        "remove_special",
        "normalize_date",
        "numeric_cleanup",
    }

    @staticmethod
    def load(path: str | Path) -> RuleSet:
        """Load a rule set from a JSON file."""
        path = Path(path)
        logger.info("Loading rule set from %s", path)
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        rule_set = RuleSet.from_dict(data)
        RuleEngine.validate(rule_set)
        return rule_set

    @staticmethod
    def save(rule_set: RuleSet, path: str | Path) -> Path:
        """Persist a rule set to JSON."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(rule_set.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info("Saved rule set to %s", path)
        return path

    @staticmethod
    def clone(rule_set: RuleSet, new_name: str, bump_version: bool = True) -> RuleSet:
        """Create a copy of a rule set with a new name."""
        data = rule_set.to_dict()
        data["rule_name"] = new_name
        if bump_version:
            try:
                major, minor = rule_set.version.split(".")
                data["version"] = f"{major}.{int(minor) + 1}"
            except ValueError:
                data["version"] = rule_set.version + ".1"
        return RuleSet.from_dict(data)

    @staticmethod
    def validate(rule_set: RuleSet) -> None:
        """Validate rule set structure and supported operations."""
        if not rule_set.rule_name.strip():
            raise ValueError("rule_name is required")
        if not rule_set.columns:
            raise ValueError("At least one column rule is required")

        field_ids = set()
        for col in rule_set.columns:
            if not col.field_id.strip():
                raise ValueError("Each column must have a field_id")
            if col.field_id in field_ids:
                raise ValueError(f"Duplicate field_id: {col.field_id}")
            field_ids.add(col.field_id)
            for op in col.cleaning:
                if op not in RuleEngine.SUPPORTED_CLEANING:
                    raise ValueError(f"Unsupported cleaning rule: {op}")

        for dup in rule_set.duplicate_rules:
            if not dup.fields:
                raise ValueError(f"Duplicate rule '{dup.name}' requires fields")

    @staticmethod
    def list_library() -> list[dict[str, Any]]:
        """List saved rule sets in the default library."""
        lib = rules_library_dir()
        entries: list[dict[str, Any]] = []
        for path in sorted(lib.glob("*.json")):
            try:
                rs = RuleEngine.load(path)
                entries.append(
                    {
                        "path": str(path),
                        "rule_name": rs.rule_name,
                        "version": rs.version,
                        "columns": len(rs.columns),
                    }
                )
            except Exception as exc:
                logger.warning("Skipping invalid rule file %s: %s", path, exc)
        return entries
