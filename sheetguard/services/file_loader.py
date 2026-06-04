"""File import utilities."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from sheetguard.models.rules import RuleSet

logger = logging.getLogger(__name__)


class FileLoader:
    """Load Excel and CSV spreadsheets into DataFrames."""

    @staticmethod
    def load(path: str | Path, rule_set: RuleSet | None = None) -> pd.DataFrame:
        """Load a spreadsheet file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # header_row: -1 means No Header (use letters), 0 means Row 1 is Header, etc.
        header_row = rule_set.header_row if rule_set else 0
        end_row = rule_set.end_row if rule_set else None
        sheet = rule_set.sheet_name if rule_set else 0

        # Map -1 to None for pandas (means no header in file)
        pandas_header = None if header_row == -1 else header_row

        # Calculate how many rows to read if an end row is specified
        nrows = None
        if end_row:
            # If no header, data starts at row 1.
            # If header_row=0, data starts at row 2.
            data_start_row = (header_row if header_row >= 0 else 0) + 2
            if end_row >= data_start_row:
                nrows = end_row - data_start_row + 1
            else:
                nrows = 0

        suffix = path.suffix.lower()
        logger.info("Loading %s (range: %s to %s)", path, header_row + 1, end_row or "EOF")

        if suffix == ".csv":
            df = pd.read_csv(
                path, 
                header=pandas_header, 
                nrows=nrows,
                dtype=object, 
                keep_default_na=False
            )
        elif suffix in {".xlsx", ".xls"}:
            df = pd.read_excel(
                path,
                sheet_name=sheet or 0,
                header=pandas_header,
                nrows=nrows,
                dtype=object,
                engine="openpyxl",
            )
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        df = df.dropna(how="all").reset_index(drop=True)
        
        # If No Header was selected, map columns to Excel-style letters (A, B, C...)
        if header_row == -1:
            from openpyxl.utils import get_column_letter
            df.columns = [get_column_letter(i + 1) for i in range(len(df.columns))]
        else:
            df.columns = [str(c).strip() for c in df.columns]
            
        logger.info("Loaded %d rows x %d columns", len(df), len(df.columns))
        return df
