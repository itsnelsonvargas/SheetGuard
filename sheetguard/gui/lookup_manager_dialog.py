"""Lookup table manager dialog."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sheetguard.services.lookup_service import LookupMetadata, LookupService
from sheetguard.utils.column_utils import coerce_cell


class LookupTableManagerDialog(QDialog):
    """Import, preview, and manage lookup/reference tables."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Lookup Table Manager")
        self.setMinimumSize(960, 640)
        self.setModal(True)

        self._service = LookupService()
        self._source_path: Path | None = None
        self._source_df: pd.DataFrame | None = None

        self._build_ui()
        self._refresh_saved_lookups()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        intro = QLabel(
            "Use lookup tables as reference lists for validation, such as valid schools, municipalities, statuses, or grade levels."
        )
        intro.setStyleSheet("font-weight: 600; color: #64748B;")
        intro.setWordWrap(True)
        root.addWidget(intro)

        steps = QLabel(
            "Workflow: 1. Choose a source file  2. Pick the sheet if needed  3. Select the key column  4. Preview values  5. Save the lookup"
        )
        steps.setStyleSheet("color: #64748B; font-size: 11px;")
        steps.setWordWrap(True)
        root.addWidget(steps)

        splitter = QSplitter()
        root.addWidget(splitter)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("Saved Lookups"))
        saved_help = QLabel("Saved lookups are stored in the app library and can be reused by rule sets.")
        saved_help.setStyleSheet("color: #64748B; font-size: 11px;")
        saved_help.setWordWrap(True)
        left_layout.addWidget(saved_help)
        self.saved_list = QListWidget()
        self.saved_list.setToolTip("Select a saved lookup to view its settings or preview its stored values.")
        self.saved_list.currentRowChanged.connect(self._on_saved_selected)
        left_layout.addWidget(self.saved_list)

        saved_btns = QHBoxLayout()
        self.btn_preview_saved = QPushButton("👁 Preview")
        self.btn_preview_saved.setObjectName("secondary")
        self.btn_preview_saved.setToolTip("Show the normalized values that were saved for the selected lookup.")
        self.btn_delete_saved = QPushButton("🗑️ Delete")
        self.btn_delete_saved.setObjectName("danger")
        self.btn_delete_saved.setToolTip("Remove the selected lookup from the app library.")
        self.btn_preview_saved.clicked.connect(self._preview_selected_saved)
        self.btn_delete_saved.clicked.connect(self._delete_selected_saved)
        saved_btns.addWidget(self.btn_preview_saved)
        saved_btns.addWidget(self.btn_delete_saved)
        left_layout.addLayout(saved_btns)
        splitter.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)

        import_group = QGroupBox("Import Lookup Source")
        import_layout = QFormLayout(import_group)
        import_help = QLabel(
            "A lookup source can be CSV, TSV, TXT, XLSX, XLS, or JSON. The key column is the list of valid values SheetGuard will check against."
        )
        import_help.setStyleSheet("color: #64748B; font-size: 11px;")
        import_help.setWordWrap(True)
        import_layout.addRow("", import_help)
        file_row = QHBoxLayout()
        self.source_path = QLineEdit()
        self.source_path.setReadOnly(True)
        self.source_path.setPlaceholderText("Choose CSV, TSV, TXT, XLSX, XLS, or JSON")
        self.source_path.setToolTip("The source file to import. SheetGuard copies and normalizes it into the app lookup library.")
        self.btn_choose_file = QPushButton("📂 Choose File")
        self.btn_choose_file.setToolTip("Browse for a lookup source file to import.")
        self.btn_choose_file.clicked.connect(self._choose_file)
        file_row.addWidget(self.source_path)
        file_row.addWidget(self.btn_choose_file)
        import_layout.addRow("Source", file_row)

        self.sheet_combo = QComboBox()
        self.sheet_combo.currentTextChanged.connect(self._load_selected_sheet)
        import_layout.addRow("Sheet", self.sheet_combo)

        self.lookup_name = QLineEdit()
        self.lookup_name.setPlaceholderText("e.g. Municipalities")
        import_layout.addRow("Name", self.lookup_name)

        self.key_column = QComboBox()
        self.key_column.currentTextChanged.connect(self._refresh_source_preview)
        import_layout.addRow("Key Column", self.key_column)

        self.match_mode = QComboBox()
        self.match_mode.addItems(["fuzzy", "exact"])
        import_layout.addRow("Match Mode", self.match_mode)

        self.fuzzy_threshold = QSpinBox()
        self.fuzzy_threshold.setRange(0, 100)
        self.fuzzy_threshold.setValue(90)
        self.fuzzy_threshold.setSuffix("%")
        import_layout.addRow("Fuzzy Threshold", self.fuzzy_threshold)

        self.case_sensitive = QCheckBox("Case sensitive")
        self.trim_spaces = QCheckBox("Trim spaces before matching")
        self.trim_spaces.setChecked(True)
        import_layout.addRow("Case", self.case_sensitive)
        import_layout.addRow("Cleanup", self.trim_spaces)

        right_layout.addWidget(import_group)

        right_layout.addWidget(QLabel("Preview"))
        self.preview_table = QTableWidget()
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        right_layout.addWidget(self.preview_table)

        action_row = QHBoxLayout()
        action_row.addStretch()
        self.btn_save = QPushButton("💾 Save Lookup")
        self.btn_save.clicked.connect(self._save_lookup)
        self.btn_close = QPushButton("✖ Close")
        self.btn_close.setObjectName("secondary")
        self.btn_close.clicked.connect(self.accept)
        action_row.addWidget(self.btn_save)
        action_row.addWidget(self.btn_close)
        right_layout.addLayout(action_row)

        splitter.addWidget(right)
        splitter.setStretchFactor(1, 1)

    def _choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Lookup Table",
            "",
            "Lookup Sources (*.csv *.tsv *.txt *.xlsx *.xls *.json)",
        )
        if not path:
            return

        self._source_path = Path(path)
        self.source_path.setText(str(self._source_path))
        self.lookup_name.setText(self._source_path.stem.replace("_", " ").title())

        try:
            sheets = self._service.sheets(self._source_path)
            self.sheet_combo.blockSignals(True)
            self.sheet_combo.clear()
            if sheets:
                self.sheet_combo.addItems(sheets)
                self.sheet_combo.setEnabled(True)
            else:
                self.sheet_combo.addItem("n/a")
                self.sheet_combo.setEnabled(False)
            self.sheet_combo.blockSignals(False)
            self._load_selected_sheet()
        except Exception as exc:
            QMessageBox.critical(self, "Import Lookup", str(exc))

    def _load_selected_sheet(self) -> None:
        if not self._source_path:
            return
        sheet = self.sheet_combo.currentText() if self.sheet_combo.isEnabled() else None
        try:
            self._source_df = self._service.load_source(self._source_path, sheet=sheet)
            self.key_column.blockSignals(True)
            self.key_column.clear()
            self.key_column.addItems([str(c) for c in self._source_df.columns])
            self.key_column.blockSignals(False)
            self._refresh_source_preview()
        except Exception as exc:
            QMessageBox.critical(self, "Load Lookup", str(exc))

    def _refresh_source_preview(self) -> None:
        if self._source_df is None:
            return
        key = self.key_column.currentText()
        if key and key in self._source_df.columns:
            preview = self._source_df[[key]].head(100)
        else:
            preview = self._source_df.head(100)
        self._set_preview(preview)

    def _refresh_saved_lookups(self) -> None:
        self.saved_list.clear()
        for entry in self._service.list_entries():
            self.saved_list.addItem(
                f"{entry.name} | {entry.key_column} | {entry.match_mode} {entry.fuzzy_threshold:.0f}%"
            )
            self.saved_list.item(self.saved_list.count() - 1).setData(256, entry)

    def _on_saved_selected(self, row: int | None = None) -> None:
        item = self.saved_list.currentItem()
        if not item:
            return
        metadata = item.data(256)
        if isinstance(metadata, LookupMetadata):
            self._show_metadata(metadata)

    def _show_metadata(self, metadata: LookupMetadata) -> None:
        self.lookup_name.setText(metadata.name)
        self.key_column.clear()
        self.key_column.addItem(metadata.key_column)
        self.match_mode.setCurrentText(metadata.match_mode)
        self.fuzzy_threshold.setValue(int(metadata.fuzzy_threshold))
        self.case_sensitive.setChecked(metadata.case_sensitive)
        self.trim_spaces.setChecked(metadata.trim_spaces)

    def _preview_selected_saved(self) -> None:
        item = self.saved_list.currentItem()
        if not item:
            return
        metadata = item.data(256)
        if not isinstance(metadata, LookupMetadata):
            return
        try:
            self._set_preview(self._service.preview_saved(metadata))
        except Exception as exc:
            QMessageBox.critical(self, "Preview Lookup", str(exc))

    def _delete_selected_saved(self) -> None:
        item = self.saved_list.currentItem()
        if not item:
            return
        metadata = item.data(256)
        if not isinstance(metadata, LookupMetadata):
            return
        ans = QMessageBox.question(
            self,
            "Delete Lookup",
            f"Delete lookup table '{metadata.name}'?",
        )
        if ans == QMessageBox.StandardButton.Yes:
            self._service.delete(metadata.name)
            self._refresh_saved_lookups()
            self.preview_table.clear()

    def _save_lookup(self) -> None:
        if self._source_path is None or self._source_df is None:
            QMessageBox.warning(self, "Save Lookup", "Choose a lookup source file first.")
            return
        name = self.lookup_name.text().strip()
        key = self.key_column.currentText().strip()
        if not name or not key:
            QMessageBox.warning(self, "Save Lookup", "Provide a name and key column.")
            return
        try:
            sheet = self.sheet_combo.currentText() if self.sheet_combo.isEnabled() else None
            metadata = self._service.save_lookup(
                name=name,
                source_path=self._source_path,
                df=self._source_df,
                key_column=key,
                sheet=sheet,
                fuzzy_threshold=float(self.fuzzy_threshold.value()),
                match_mode=self.match_mode.currentText(),
                case_sensitive=self.case_sensitive.isChecked(),
                trim_spaces=self.trim_spaces.isChecked(),
            )
            self._refresh_saved_lookups()
            QMessageBox.information(self, "Lookup Saved", f"Saved lookup table: {metadata.name}")
        except Exception as exc:
            QMessageBox.critical(self, "Save Lookup", str(exc))

    def _set_preview(self, df: pd.DataFrame) -> None:
        self.preview_table.clear()
        if df is None or df.empty:
            self.preview_table.setRowCount(0)
            self.preview_table.setColumnCount(0)
            return

        self.preview_table.setRowCount(len(df))
        self.preview_table.setColumnCount(len(df.columns))
        self.preview_table.setHorizontalHeaderLabels([str(c) for c in df.columns])
        for r in range(len(df)):
            for c, col in enumerate(df.columns):
                self.preview_table.setItem(r, c, QTableWidgetItem(str(coerce_cell(df.iloc[r][col]))))
        self.preview_table.resizeColumnsToContents()
