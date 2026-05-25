"""File import utilities."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from sheetguard.models.rules import RuleSet

logger = logging.getLogger(__name__)


class FileLoader:
    """Load Excel and CSV masterlists into DataFrames."""

    @staticmethod
    def load(path: str | Path, rule_set: RuleSet | None = None) -> pd.DataFrame:
        """Load a masterlist file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        header_row = rule_set.header_row if rule_set else 0
        sheet = rule_set.sheet_name if rule_set else 0

        suffix = path.suffix.lower()
        logger.info("Loading %s", path)

        if suffix == ".csv":
            df = pd.read_csv(path, header=header_row, dtype=object, keep_default_na=False)
        elif suffix in {".xlsx", ".xls"}:
            df = pd.read_excel(
                path,
                sheet_name=sheet or 0,
                header=header_row,
                dtype=object,
                engine="openpyxl",
            )
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        df = df.dropna(how="all").reset_index(drop=True)
        df.columns = [str(c).strip() for c in df.columns]
        logger.info("Loaded %d rows x %d columns", len(df), len(df.columns))
        return df
