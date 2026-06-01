"""Lookup table manager dialog."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
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
        self.setMinimumSize(1060, 700)
        self.setModal(True)

        self._service = LookupService()
        self._source_path: Path | None = None
        self._source_df: pd.DataFrame | None = None

        self._build_ui()
        self._refresh_saved_lookups()

    # ── UI Construction ──────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        intro = QLabel(
            "Use lookup tables as reference lists for validation, such as valid schools, "
            "municipalities, statuses, or grade levels."
        )
        intro.setStyleSheet("font-weight: 600; color: #64748B;")
        intro.setWordWrap(True)
        root.addWidget(intro)

        # ── Main horizontal splitter ─────────────────────────────────
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(main_splitter, 1)

        # ── LEFT PANEL: Saved lookups + preview ──────────────────────
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Saved lookups list
        saved_header = QLabel("📚 Saved Lookups")
        saved_header.setStyleSheet("font-weight: 700; font-size: 13px;")
        left_layout.addWidget(saved_header)

        saved_help = QLabel(
            "Select a lookup to preview its values. "
            "Saved lookups can be reused by rule sets."
        )
        saved_help.setStyleSheet("color: #64748B; font-size: 11px;")
        saved_help.setWordWrap(True)
        left_layout.addWidget(saved_help)

        self.saved_list = QListWidget()
        self.saved_list.setObjectName("savedLookups")
        self.saved_list.setToolTip(
            "Select a saved lookup to view its settings and preview its stored values."
        )
        self.saved_list.currentRowChanged.connect(self._on_saved_selected)
        left_layout.addWidget(self.saved_list)

        # Buttons row
        saved_btns = QHBoxLayout()
        self.btn_delete_saved = QPushButton("🗑️ Delete")
        self.btn_delete_saved.setObjectName("danger")
        self.btn_delete_saved.setToolTip("Remove the selected lookup from the app library.")
        self.btn_delete_saved.clicked.connect(self._delete_selected_saved)
        saved_btns.addStretch()
        saved_btns.addWidget(self.btn_delete_saved)
        left_layout.addLayout(saved_btns)

        # ── Saved-lookup preview (below the list) ────────────────────
        left_splitter = QSplitter(Qt.Orientation.Vertical)

        # Top part: the list + buttons we just built
        left_splitter.addWidget(left)

        # Bottom part: preview of saved lookup
        saved_preview_container = QWidget()
        saved_preview_layout = QVBoxLayout(saved_preview_container)
        saved_preview_layout.setContentsMargins(0, 4, 0, 0)

        self.saved_preview_header = QLabel("Preview")
        self.saved_preview_header.setStyleSheet("font-weight: 700; font-size: 13px;")
        saved_preview_layout.addWidget(self.saved_preview_header)

        self.saved_meta_label = QLabel("")
        self.saved_meta_label.setStyleSheet("color: #64748B; font-size: 11px;")
        self.saved_meta_label.setWordWrap(True)
        saved_preview_layout.addWidget(self.saved_meta_label)

        self.saved_preview_table = QTableWidget()
        self.saved_preview_table.setObjectName("savedPreviewTable")
        self.saved_preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.saved_preview_table.horizontalHeader().setStretchLastSection(True)
        self.saved_preview_table.setAlternatingRowColors(True)
        saved_preview_layout.addWidget(self.saved_preview_table, 1)

        left_splitter.addWidget(saved_preview_container)
        left_splitter.setStretchFactor(0, 2)
        left_splitter.setStretchFactor(1, 3)

        main_splitter.addWidget(left_splitter)

        # ── RIGHT PANEL: Import new lookup ───────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        import_header = QLabel("📥 Import New Lookup")
        import_header.setStyleSheet("font-weight: 700; font-size: 13px;")
        right_layout.addWidget(import_header)

        import_group = QGroupBox("Import Lookup Source")
        import_layout = QFormLayout(import_group)
        import_help = QLabel(
            "A lookup source can be CSV, TSV, TXT, XLSX, XLS, or JSON. "
            "The key column is the list of valid values SheetGuard will check against."
        )
        import_help.setStyleSheet("color: #64748B; font-size: 11px;")
        import_help.setWordWrap(True)
        import_layout.addRow("", import_help)

        file_row = QHBoxLayout()
        self.source_path = QLineEdit()
        self.source_path.setReadOnly(True)
        self.source_path.setPlaceholderText("Choose CSV, TSV, TXT, XLSX, XLS, or JSON")
        self.source_path.setToolTip(
            "The source file to import. SheetGuard copies and normalizes it into the app lookup library."
        )
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
        self.match_mode.addItems(["exact", "fuzzy"])
        self.match_mode.setCurrentText("exact")
        import_layout.addRow("Match Mode", self.match_mode)

        self.fuzzy_threshold = QSpinBox()
        self.fuzzy_threshold.setRange(0, 100)
        self.fuzzy_threshold.setValue(100)
        self.fuzzy_threshold.setSuffix("%")
        import_layout.addRow("Fuzzy Threshold", self.fuzzy_threshold)

        # Connect signals after both widgets are created
        self.match_mode.currentTextChanged.connect(self._on_match_mode_changed)
        self.fuzzy_threshold.valueChanged.connect(self._on_fuzzy_threshold_changed)

        self.case_sensitive = QCheckBox("Case sensitive")
        self.trim_spaces = QCheckBox("Trim spaces before matching")
        self.trim_spaces.setChecked(True)
        import_layout.addRow("Case", self.case_sensitive)
        import_layout.addRow("Cleanup", self.trim_spaces)

        right_layout.addWidget(import_group)

        # Source file preview
        source_preview_header = QLabel("Source Preview")
        source_preview_header.setStyleSheet("font-weight: 700; font-size: 13px;")
        right_layout.addWidget(source_preview_header)

        self.source_preview_table = QTableWidget()
        self.source_preview_table.setObjectName("sourcePreviewTable")
        self.source_preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.source_preview_table.horizontalHeader().setStretchLastSection(True)
        self.source_preview_table.setAlternatingRowColors(True)
        right_layout.addWidget(self.source_preview_table, 1)

        # Action buttons
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

        main_splitter.addWidget(right)
        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 3)

    # ── File import slots ────────────────────────────────────────────

    def _on_match_mode_changed(self, mode: str) -> None:
        """Handle match mode changes: exact mode forces 100% threshold."""
        if mode == "exact":
            if self.fuzzy_threshold.value() != 100:
                self.fuzzy_threshold.setValue(100)
        elif mode == "fuzzy":
            if self.fuzzy_threshold.value() == 100:
                self.fuzzy_threshold.setValue(90)

    def _on_fuzzy_threshold_changed(self, value: int) -> None:
        """Handle threshold changes: 100% is exact, <100% is fuzzy."""
        if value == 100:
            if self.match_mode.currentText() != "exact":
                self.match_mode.setCurrentText("exact")
        else:
            if self.match_mode.currentText() != "fuzzy":
                self.match_mode.setCurrentText("fuzzy")

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

        # Reset defaults when a new source is selected
        self.match_mode.setCurrentText("exact")
        self.fuzzy_threshold.setValue(100)

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
        self._fill_table(self.source_preview_table, preview)

    # ── Saved lookup slots ───────────────────────────────────────────

    def _refresh_saved_lookups(self) -> None:
        self.saved_list.clear()
        for entry in self._service.list_entries():
            self.saved_list.addItem(
                f"{entry.name}  •  {entry.key_column}  •  {entry.match_mode} {entry.fuzzy_threshold:.0f}%"
            )
            self.saved_list.item(self.saved_list.count() - 1).setData(256, entry)

    def _on_saved_selected(self, row: int | None = None) -> None:
        item = self.saved_list.currentItem()
        if not item:
            self._clear_saved_preview()
            return
        metadata = item.data(256)
        if isinstance(metadata, LookupMetadata):
            self._show_saved_preview(metadata)

    def _show_saved_preview(self, metadata: LookupMetadata) -> None:
        """Load and display saved lookup values + metadata summary."""
        # Update metadata summary
        parts = [
            f"<b>{metadata.name}</b>",
            f"Column: <b>{metadata.key_column}</b>",
            f"Match: <b>{metadata.match_mode}</b> ({metadata.fuzzy_threshold:.0f}%)",
            f"Case-sensitive: <b>{'Yes' if metadata.case_sensitive else 'No'}</b>",
            f"Trim spaces: <b>{'Yes' if metadata.trim_spaces else 'No'}</b>",
        ]
        self.saved_meta_label.setText("  │  ".join(parts))

        # Update form fields
        self.lookup_name.setText(metadata.name)
        self.key_column.clear()
        self.key_column.addItem(metadata.key_column)
        
        self.match_mode.blockSignals(True)
        self.fuzzy_threshold.blockSignals(True)
        self.match_mode.setCurrentText(metadata.match_mode)
        self.fuzzy_threshold.setValue(int(metadata.fuzzy_threshold))
        self.match_mode.blockSignals(False)
        self.fuzzy_threshold.blockSignals(False)

        self.case_sensitive.setChecked(metadata.case_sensitive)
        self.trim_spaces.setChecked(metadata.trim_spaces)

        # Load preview data
        try:
            df = self._service.preview_saved(metadata)
            row_count = len(df)
            self.saved_preview_header.setText(
                f"Preview  —  {row_count} value{'s' if row_count != 1 else ''}"
            )
            self._fill_table(self.saved_preview_table, df)
        except Exception as exc:
            self.saved_preview_header.setText("Preview")
            self.saved_meta_label.setText(f"⚠ Could not load preview: {exc}")
            self._fill_table(self.saved_preview_table, pd.DataFrame())

    def _clear_saved_preview(self) -> None:
        """Reset the saved-lookup preview area."""
        self.saved_preview_header.setText("Preview")
        self.saved_meta_label.setText("Select a saved lookup above to preview its values.")
        self.saved_preview_table.clear()
        self.saved_preview_table.setRowCount(0)
        self.saved_preview_table.setColumnCount(0)

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
            self._clear_saved_preview()

    # ── Save lookup ──────────────────────────────────────────────────

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

    # ── Table helper ─────────────────────────────────────────────────

    def _fill_table(self, table: QTableWidget, df: pd.DataFrame) -> None:
        """Populate a QTableWidget from a DataFrame."""
        table.clear()
        if df is None or df.empty:
            table.setRowCount(0)
            table.setColumnCount(0)
            return

        table.setRowCount(len(df))
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels([str(c) for c in df.columns])
        for r in range(len(df)):
            for c, col in enumerate(df.columns):
                table.setItem(r, c, QTableWidgetItem(str(coerce_cell(df.iloc[r][col]))))
        table.resizeColumnsToContents()
