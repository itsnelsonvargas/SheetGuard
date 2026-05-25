"""Validation results and preview tabs."""

from __future__ import annotations

from typing import Any

import pandas as pd
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTabWidget, QVBoxLayout, QWidget

from sheetguard.gui.widgets.data_table import DataTableWidget
from sheetguard.gui.widgets.summary_cards import SummaryCards
from sheetguard.models.results import ProcessingResult


class ResultsView(QWidget):
    """Main results area: summary cards + tabbed tables."""

    request_row_deletion = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.summary = SummaryCards()
        layout.addWidget(self.summary)

        self.tabs = QTabWidget()
        self.preview_table = DataTableWidget()
        self.errors_table = DataTableWidget()
        self.duplicates_table = DataTableWidget()

        self.tabs.addTab(self.preview_table, "Preview")
        self.tabs.addTab(self.errors_table, "Validation Errors")
        self.tabs.addTab(self.duplicates_table, "Duplicates")

        layout.addWidget(self.tabs)

    def _on_row_action(self, row_data: dict[str, Any]) -> None:
        if "row_number" in row_data:
            try:
                row_idx = int(row_data["row_number"]) - 1
                self.request_row_deletion.emit(row_idx)
            except (ValueError, TypeError):
                pass

    def show_result(self, result: ProcessingResult) -> None:
        self.summary.update_counts(
            errors=result.error_count,
            warnings=result.warning_count,
            duplicates=len(result.duplicates),
            corrections=len(result.corrections),
        )
        self.preview_table.set_dataframe(result.cleaned_df)
        self.errors_table.set_dataframe(self._issues_df(result))
        self.duplicates_table.set_dataframe(
            self._duplicates_df(result), 
            action_column="Delete", 
            on_action=self._on_row_action
        )

    def show_preview(self, df: pd.DataFrame) -> None:
        self.preview_table.set_dataframe(df)

    def reset(self) -> None:
        self.summary.reset()
        self.preview_table.set_dataframe(None)
        self.errors_table.set_dataframe(None)
        self.duplicates_table.set_dataframe(None)

    @staticmethod
    def _issues_df(result: ProcessingResult) -> pd.DataFrame:
        if not result.issues:
            return pd.DataFrame()
        return pd.DataFrame([i.to_dict() for i in result.issues])

    @staticmethod
    def _duplicates_df(result: ProcessingResult) -> pd.DataFrame:
        rows = []
        for g in result.duplicates:
            for idx in g.row_indices:
                row = result.cleaned_df.iloc[idx].to_dict()
                row["duplicate_rule"] = g.rule_name
                row["row_number"] = idx + 1
                rows.append(row)
        return pd.DataFrame(rows) if rows else pd.DataFrame()
