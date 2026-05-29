"""Lookup table import and library management."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from sheetguard.utils.paths import app_root, lookups_library_dir


@dataclass
class LookupMetadata:
    """Stored lookup table metadata."""

    name: str
    source_type: str
    stored_path: str
    key_column: str
    sheet: str | None = None
    match_mode: str = "fuzzy"
    case_sensitive: bool = False
    trim_spaces: bool = True
    fuzzy_threshold: float = 90.0
    original_path: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LookupMetadata:
        return cls(
            name=data["name"],
            source_type=data.get("source_type", "csv"),
            stored_path=data["stored_path"],
            key_column=data["key_column"],
            sheet=data.get("sheet"),
            match_mode=data.get("match_mode", "fuzzy"),
            case_sensitive=bool(data.get("case_sensitive", False)),
            trim_spaces=bool(data.get("trim_spaces", True)),
            fuzzy_threshold=float(data.get("fuzzy_threshold", 90.0)),
            original_path=data.get("original_path", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


class LookupSourceAdapter:
    """Base class for lookup file adapters."""

    supported_extensions: set[str] = set()

    def sheets(self, path: Path) -> list[str]:
        return []

    def load(self, path: Path, sheet: str | None = None) -> pd.DataFrame:
        raise NotImplementedError


class CsvLookupAdapter(LookupSourceAdapter):
    supported_extensions = {".csv", ".tsv", ".txt"}

    def load(self, path: Path, sheet: str | None = None) -> pd.DataFrame:
        if path.suffix.lower() == ".tsv":
            return pd.read_csv(path, dtype=object, keep_default_na=False, sep="\t")
        if path.suffix.lower() == ".txt":
            return pd.read_csv(path, dtype=object, keep_default_na=False, sep=None, engine="python")
        return pd.read_csv(path, dtype=object, keep_default_na=False)


class ExcelLookupAdapter(LookupSourceAdapter):
    supported_extensions = {".xlsx", ".xls"}

    def sheets(self, path: Path) -> list[str]:
        return list(pd.ExcelFile(path).sheet_names)

    def load(self, path: Path, sheet: str | None = None) -> pd.DataFrame:
        return pd.read_excel(path, sheet_name=sheet or 0, dtype=object, keep_default_na=False)


class JsonLookupAdapter(LookupSourceAdapter):
    supported_extensions = {".json"}

    def load(self, path: Path, sheet: str | None = None) -> pd.DataFrame:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return pd.DataFrame(data)
        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, list):
                    return pd.DataFrame(value)
            return pd.DataFrame([data])
        raise ValueError("JSON lookup must contain an object, array, or object with an array value.")


class LookupService:
    """CRUD operations and import normalization for lookup tables."""

    def __init__(self, library_dir: Path | None = None) -> None:
        self.library_dir = library_dir or lookups_library_dir()
        self.library_dir.mkdir(parents=True, exist_ok=True)
        self.adapters: list[LookupSourceAdapter] = [
            CsvLookupAdapter(),
            ExcelLookupAdapter(),
            JsonLookupAdapter(),
        ]

    def adapter_for(self, path: str | Path) -> LookupSourceAdapter:
        suffix = Path(path).suffix.lower()
        for adapter in self.adapters:
            if suffix in adapter.supported_extensions:
                return adapter
        raise ValueError(f"Unsupported lookup file type: {suffix}")

    def sheets(self, path: str | Path) -> list[str]:
        return self.adapter_for(path).sheets(Path(path))

    def load_source(self, path: str | Path, sheet: str | None = None) -> pd.DataFrame:
        df = self.adapter_for(path).load(Path(path), sheet=sheet)
        df = df.dropna(how="all").reset_index(drop=True)
        df.columns = [str(c).strip() for c in df.columns]
        return df

    def list_entries(self) -> list[LookupMetadata]:
        entries: list[LookupMetadata] = []
        for path in sorted(self.library_dir.glob("*.json")):
            try:
                entries.append(LookupMetadata.from_dict(json.loads(path.read_text(encoding="utf-8"))))
            except Exception:
                continue
        return entries

    def save_lookup(
        self,
        *,
        name: str,
        source_path: str | Path,
        df: pd.DataFrame,
        key_column: str,
        sheet: str | None,
        fuzzy_threshold: float,
        match_mode: str = "fuzzy",
        case_sensitive: bool = False,
        trim_spaces: bool = True,
    ) -> LookupMetadata:
        if key_column not in df.columns:
            raise ValueError(f"Key column '{key_column}' was not found.")

        safe_name = self._safe_name(name)
        csv_path = self.library_dir / f"{safe_name}.csv"
        meta_path = self.library_dir / f"{safe_name}.json"
        source_path = Path(source_path)

        normalized = pd.DataFrame({key_column: df[key_column].dropna().astype(str)})
        if trim_spaces:
            normalized[key_column] = normalized[key_column].str.strip()
        if not case_sensitive:
            normalized[key_column] = normalized[key_column].str.upper()
        normalized = normalized[normalized[key_column] != ""].drop_duplicates().reset_index(drop=True)
        normalized.to_csv(csv_path, index=False)

        original_copy = self.library_dir / f"{safe_name}_source{source_path.suffix.lower()}"
        try:
            shutil.copy2(source_path, original_copy)
        except OSError:
            original_copy = source_path

        now = datetime.now().isoformat(timespec="seconds")
        existing = self._load_metadata(meta_path)
        try:
            stored_path = str(csv_path.relative_to(app_root()))
        except ValueError:
            stored_path = str(csv_path)

        metadata = LookupMetadata(
            name=name.strip(),
            source_type=source_path.suffix.lower().lstrip("."),
            stored_path=stored_path,
            key_column=key_column,
            sheet=sheet,
            match_mode=match_mode,
            case_sensitive=case_sensitive,
            trim_spaces=trim_spaces,
            fuzzy_threshold=fuzzy_threshold,
            original_path=str(original_copy),
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        meta_path.write_text(json.dumps(asdict(metadata), indent=2), encoding="utf-8")
        return metadata

    def delete(self, name: str) -> None:
        safe_name = self._safe_name(name)
        for path in self.library_dir.glob(f"{safe_name}*"):
            if path.is_file():
                path.unlink(missing_ok=True)

    def preview_saved(self, metadata: LookupMetadata, limit: int = 100) -> pd.DataFrame:
        path = Path(metadata.stored_path)
        if not path.is_absolute():
            path = app_root() / path
        return pd.read_csv(path, dtype=object, keep_default_na=False).head(limit)

    @staticmethod
    def _safe_name(name: str) -> str:
        slug = re.sub(r"[^\w\-]+", "_", name.strip().lower())
        return slug or "lookup"

    @staticmethod
    def _load_metadata(path: Path) -> LookupMetadata | None:
        if not path.exists():
            return None
        try:
            return LookupMetadata.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            return None
