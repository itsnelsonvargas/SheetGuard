#!/usr/bin/env python3
"""Generate sample SheetGuard output workbooks for documentation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sheetguard.core.exporter import WorkbookExporter
from sheetguard.core.rule_engine import RuleEngine
from sheetguard.services.pipeline import ProcessingPipeline
from sheetguard.utils.logging_config import setup_logging


def main() -> None:
    setup_logging()
    rule_path = ROOT / "resources" / "rules" / "tbtp_masterlist.json"
    data_path = ROOT / "resources" / "samples" / "sample_masterlist.csv"
    out_dir = ROOT / "resources" / "examples"
    out_dir.mkdir(parents=True, exist_ok=True)

    rule_set = RuleEngine.load(rule_path)
    pipeline = ProcessingPipeline(rule_set)
    result = pipeline.run(str(data_path))

    exporter = WorkbookExporter()
    exporter.export_full_report(result, out_dir / "example_full_report.xlsx")
    exporter.export_cleaned_only(result, out_dir / "example_cleaned_data.xlsx")
    exporter.export_validation_report(result, out_dir / "example_validation_report.xlsx")
    dup_df = exporter._duplicates_df(result)
    exporter.export_duplicate_report(result, dup_df, out_dir / "example_duplicate_report.xlsx")
    print(f"Generated example reports in {out_dir}")


if __name__ == "__main__":
    main()
