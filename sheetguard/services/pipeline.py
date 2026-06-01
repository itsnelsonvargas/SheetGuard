"""Orchestrates the full cleaning and validation pipeline."""

from __future__ import annotations

import logging
from typing import Callable

import pandas as pd

from sheetguard.core.cleaner import DataCleaner
from sheetguard.core.duplicate_checker import DuplicateChecker
from sheetguard.core.validator import DataValidator
from sheetguard.models.results import ProcessingResult
from sheetguard.models.rules import RuleSet
from sheetguard.services.file_loader import FileLoader

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, str], None]


class ProcessingPipeline:
    """End-to-end processing: load → clean → validate → duplicates."""

    def __init__(self, rule_set: RuleSet) -> None:
        self.rule_set = rule_set

    def run(
        self,
        source: str | pd.DataFrame,
        progress: ProgressCallback | None = None,
    ) -> ProcessingResult:
        """Execute the pipeline and return aggregated results."""
        def report(pct: int, msg: str) -> None:
            if progress:
                progress(pct, msg)
            logger.info("[%d%%] %s", pct, msg)

        report(5, "Loading data...")
        if isinstance(source, pd.DataFrame):
            original_df = source.copy()
        else:
            original_df = FileLoader.load(source, self.rule_set)

        report(25, "Cleaning data...")
        cleaner = DataCleaner(self.rule_set)
        cleaned_df = cleaner.clean(original_df)

        report(50, "Validating data...")
        validator = DataValidator(self.rule_set)
        validator.load_lookups()
        issues = validator.validate(cleaned_df, original_df)

        report(75, "Detecting duplicates...")
        dup_checker = DuplicateChecker(self.rule_set)
        duplicates = dup_checker.find_duplicates(cleaned_df)

        report(95, "Building summary...")
        summary = {
            "total_rows": len(cleaned_df),
            "total_columns": len(cleaned_df.columns),
            "rule_name": self.rule_set.rule_name,
        }

        result = ProcessingResult(
            cleaned_df=cleaned_df,
            original_df=original_df,
            issues=issues,
            duplicates=duplicates,
            corrections=cleaner.corrections,
            summary=summary,
            rule_set=self.rule_set,
        )

        report(100, "Complete")
        logger.info(
            "Pipeline done: %d errors, %d warnings, %d duplicate groups",
            result.error_count,
            result.warning_count,
            len(duplicates),
        )
        return result
