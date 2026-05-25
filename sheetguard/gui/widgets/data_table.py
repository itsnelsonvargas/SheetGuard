"""Searchable pandas-backed table widget."""

from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sheetguard.utils.column_utils import coerce_cell


class DataTableWidget(QWidget):
    """Table with search/filter for preview and results."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        bar = QHBoxLayout()
        bar.addWidget(QLabel("Search:"))
        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter rows...")
        self._search.textChanged.connect(self._apply_filter)
        bar.addWidget(self._search)
        layout.addLayout(bar)

        self._table = QTableWidget()
        self._table.setSortingEnabled(True)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self._table)

        self._df: pd.DataFrame | None = None
        self._action_col_name: str | None = None
        self._action_callback: callable | None = None

    def set_dataframe(self, df: pd.DataFrame | None, action_column: str | None = None, on_action: callable | None = None) -> None:
        self._df = df.copy() if df is not None else None
        self._action_col_name = action_column
        self._action_callback = on_action
        self._search.clear()
        self._render(df)

    def _render(self, df: pd.DataFrame | None) -> None:
        self._table.setSortingEnabled(False)
        self._table.clear()
        if df is None or df.empty:
            self._table.setRowCount(0)
            self._table.setColumnCount(0)
            return

        cols = list(df.columns)
        if self._action_col_name:
            cols.append(self._action_col_name)

        self._table.setRowCount(len(df))
        self._table.setColumnCount(len(cols))
        self._table.setHorizontalHeaderLabels([str(c) for c in cols])

        for r in range(len(df)):
            for c, col in enumerate(df.columns):
                val = coerce_cell(df.iloc[r, c])
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(r, c, item)
            
            if self._action_col_name:
                btn = QPushButton(self._action_col_name)
                if "Delete" in self._action_col_name:
                    btn.setObjectName("danger")
                
                # Capture row data for callback
                row_data = df.iloc[r].to_dict()
                btn.clicked.connect(lambda checked=False, d=row_data: self._action_callback(d))
                self._table.setCellWidget(r, len(cols) - 1, btn)

        self._table.resizeColumnsToContents()
        self._table.setSortingEnabled(True)

    def _apply_filter(self, text: str) -> None:
        if self._df is None:
            return
        if not text.strip():
            self._render(self._df)
            return
        mask = self._df.astype(str).apply(
            lambda row: row.str.contains(text, case=False, na=False).any(),
            axis=1,
        )
        self._render(self._df[mask])
