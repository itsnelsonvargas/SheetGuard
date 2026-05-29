"""Rule set data models (JSON-serializable)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LookupSource:
    """External lookup file configuration."""

    name: str
    path: str
    key_column: str
    value_column: str | None = None
    sheet: str | None = None
    match_mode: str = "fuzzy"
    fuzzy_threshold: float = 90.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LookupSource:
        return cls(
            name=data["name"],
            path=data["path"],
            key_column=data["key_column"],
            value_column=data.get("value_column"),
            sheet=data.get("sheet"),
            match_mode=data.get("match_mode", "fuzzy"),
            fuzzy_threshold=float(data.get("fuzzy_threshold", 90.0)),
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "name": self.name,
            "path": self.path,
            "key_column": self.key_column,
            "match_mode": self.match_mode,
        }
        if self.value_column:
            out["value_column"] = self.value_column
        if self.sheet:
            out["sheet"] = self.sheet
        if self.fuzzy_threshold != 90.0:
            out["fuzzy_threshold"] = self.fuzzy_threshold
        return out


@dataclass
class ColumnRule:
    """Per-column cleaning and validation configuration."""

    field_id: str
    column: str
    required: bool = False
    cleaning: list[str] = field(default_factory=list)
    allowed_values: list[str] | None = None
    regex: str | None = None
    min_length: int | None = None
    max_length: int | None = None
    min_value: float | None = None
    max_value: float | None = None
    date_format: str | None = None
    lookup: str | None = None
    warning_only: bool = False
    validate_email: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ColumnRule:
        return cls(
            field_id=data["field_id"],
            column=data["column"],
            required=bool(data.get("required", False)),
            cleaning=list(data.get("cleaning", [])),
            allowed_values=data.get("allowed_values"),
            regex=data.get("regex"),
            min_length=data.get("min_length"),
            max_length=data.get("max_length"),
            min_value=data.get("min_value"),
            max_value=data.get("max_value"),
            date_format=data.get("date_format"),
            lookup=data.get("lookup"),
            warning_only=bool(data.get("warning_only", False)),
            validate_email=bool(data.get("validate_email", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "field_id": self.field_id,
            "column": self.column,
        }
        if self.required:
            out["required"] = True
        if self.validate_email:
            out["validate_email"] = True
        if self.cleaning:
            out["cleaning"] = self.cleaning
        if self.allowed_values is not None:
            out["allowed_values"] = self.allowed_values
        if self.regex:
            out["regex"] = self.regex
        if self.min_length is not None:
            out["min_length"] = self.min_length
        if self.max_length is not None:
            out["max_length"] = self.max_length
        if self.min_value is not None:
            out["min_value"] = self.min_value
        if self.max_value is not None:
            out["max_value"] = self.max_value
        if self.date_format:
            out["date_format"] = self.date_format
        if self.lookup:
            out["lookup"] = self.lookup
        if self.warning_only:
            out["warning_only"] = True
        return out


@dataclass
class DuplicateRule:
    """Composite key definition for duplicate detection."""

    name: str
    fields: list[str]
    keep: str = "all"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DuplicateRule:
        return cls(
            name=data["name"],
            fields=list(data["fields"]),
            keep=data.get("keep", "all"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "fields": self.fields, "keep": self.keep}


@dataclass
class RuleSet:
    """Complete rule configuration for a spreadsheet template."""

    rule_name: str
    version: str = "1.0"
    description: str = ""
    columns: list[ColumnRule] = field(default_factory=list)
    duplicate_rules: list[DuplicateRule] = field(default_factory=list)
    lookups: list[LookupSource] = field(default_factory=list)
    header_row: int = 0
    sheet_name: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuleSet:
        return cls(
            rule_name=data["rule_name"],
            version=data.get("version", "1.0"),
            description=data.get("description", ""),
            columns=[ColumnRule.from_dict(c) for c in data.get("columns", [])],
            duplicate_rules=[
                DuplicateRule.from_dict(d) for d in data.get("duplicate_rules", [])
            ],
            lookups=[LookupSource.from_dict(l) for l in data.get("lookups", [])],
            header_row=int(data.get("header_row", 0)),
            sheet_name=data.get("sheet_name"),
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "rule_name": self.rule_name,
            "version": self.version,
            "columns": [c.to_dict() for c in self.columns],
        }
        if self.description:
            out["description"] = self.description
        if self.duplicate_rules:
            out["duplicate_rules"] = [d.to_dict() for d in self.duplicate_rules]
        if self.lookups:
            out["lookups"] = [l.to_dict() for l in self.lookups]
        if self.header_row:
            out["header_row"] = self.header_row
        if self.sheet_name:
            out["sheet_name"] = self.sheet_name
        return out