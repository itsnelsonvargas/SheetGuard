"""Main application window."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QThread, Signal, Slot, Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from sheetguard.core.exporter import WorkbookExporter
from sheetguard.core.rule_engine import RuleEngine
from sheetguard.gui.results_view import ResultsView
from sheetguard.gui.rule_builder import RuleBuilderPanel
from sheetguard.gui.theme import apply_theme
from sheetguard.gui.widgets.file_drop import FileDropZone
from sheetguard.models.results import ProcessingResult
from sheetguard.models.rules import RuleSet
from sheetguard.services.pipeline import ProcessingPipeline
from sheetguard.services.rule_service import RuleService
from sheetguard.utils.paths import resource_path

logger = logging.getLogger(__name__)


class ProcessingWorker(QThread):
    """Background thread for pipeline execution."""

    progress = Signal(int, str)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, rule_set: RuleSet, file_path: str) -> None:
        super().__init__()
        self.rule_set = rule_set
        self.file_path = file_path

    def run(self) -> None:
        try:
            pipeline = ProcessingPipeline(self.rule_set)

            def on_progress(pct: int, msg: str) -> None:
                self.progress.emit(pct, msg)

            result = pipeline.run(self.file_path, progress=on_progress)
            self.finished_ok.emit(result)
        except Exception as exc:
            logger.exception("Processing failed")
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    """Primary application window with sidebar layout."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SheetGuard")
        self.resize(1280, 800)

        self._rule_service = RuleService()
        self._rule_set: RuleSet | None = None
        self._file_path: str | None = None
        self._result: ProcessingResult | None = None
        self._worker: ProcessingWorker | None = None
        self._dark_mode = True

        self._build_ui()
        self._load_default_rule()
        self._refresh_library()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter()
        root.addWidget(splitter)

        sidebar_scroll = QScrollArea()
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setMaximumWidth(360)
        sidebar_scroll.setMinimumWidth(300)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)

        sidebar_layout.addWidget(QLabel("File Upload"))
        self.file_drop = FileDropZone()
        self.file_drop.file_selected.connect(self._on_file_selected)
        sidebar_layout.addWidget(self.file_drop)

        btn_browse = QPushButton("Browse File...")
        btn_browse.setObjectName("secondary")
        btn_browse.clicked.connect(self._browse_file)
        sidebar_layout.addWidget(btn_browse)

        sidebar_layout.addWidget(QLabel("Data Start Row"))
        start_row_layout = QHBoxLayout()
        self.start_row_spin = QSpinBox()
        self.start_row_spin.setMinimum(1)
        self.start_row_spin.setMaximum(9999)
        self.start_row_spin.setValue(1)
        self.start_row_spin.setToolTip("Row number where data starts (1 = first row, 2 = second row, etc.)")
        start_row_layout.addWidget(self.start_row_spin)
        self.btn_confirm_start_row = QPushButton("Confirm")
        self.btn_confirm_start_row.setObjectName("secondary")
        self.btn_confirm_start_row.clicked.connect(self._on_confirm_start_row)
        start_row_layout.addWidget(self.btn_confirm_start_row)
        sidebar_layout.addLayout(start_row_layout)

        sidebar_layout.addWidget(QLabel("Rule Library"))
        self.library_list = QListWidget()
        self.library_list.currentItemChanged.connect(self._on_library_selected)
        sidebar_layout.addWidget(self.library_list)

        lib_btns = QHBoxLayout()
        self.btn_import_rule = QPushButton("Import")
        self.btn_export_rule = QPushButton("Export")
        self.btn_clone_rule = QPushButton("Clone")
        for b in (self.btn_import_rule, self.btn_export_rule, self.btn_clone_rule):
            b.setObjectName("secondary")
            lib_btns.addWidget(b)
        sidebar_layout.addLayout(lib_btns)

        self.rule_builder = RuleBuilderPanel()
        self.rule_builder.rule_changed.connect(self._on_rule_changed)
        sidebar_layout.addWidget(self.rule_builder)

        sidebar_layout.addWidget(QLabel("Processing"))
        self.btn_process = QPushButton("Run Clean & Validate")
        sidebar_layout.addWidget(self.btn_process)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%p %")
        self.progress.setTextVisible(True)
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress.setFixedHeight(24)
        sidebar_layout.addWidget(self.progress)

        sidebar_layout.addWidget(QLabel("Export"))
        self.btn_export_full = QPushButton("Export Full Report")
        self.btn_export_clean = QPushButton("Export Cleaned Data")
        self.btn_export_errors = QPushButton("Export Validation Report")
        self.btn_export_dups = QPushButton("Export Duplicate Report")
        for b in (
            self.btn_export_clean,
            self.btn_export_errors,
            self.btn_export_dups,
        ):
            b.setObjectName("secondary")
        sidebar_layout.addWidget(self.btn_export_full)
        sidebar_layout.addWidget(self.btn_export_clean)
        sidebar_layout.addWidget(self.btn_export_errors)
        sidebar_layout.addWidget(self.btn_export_dups)

        self.btn_theme = QPushButton("Dark Mode")
        self.btn_theme.setObjectName("secondary")
        self.btn_theme.setCheckable(True)
        self.btn_theme.setChecked(self._dark_mode)
        sidebar_layout.addWidget(self.btn_theme)
        sidebar_layout.addStretch()

        sidebar_scroll.setWidget(sidebar)
        splitter.addWidget(sidebar_scroll)

        self.results_view = ResultsView()
        splitter.addWidget(self.results_view)
        splitter.setStretchFactor(1, 1)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

        self.btn_process.clicked.connect(self._run_processing)
        self.btn_import_rule.clicked.connect(self._import_rule)
        self.btn_export_rule.clicked.connect(self._export_rule)
        self.btn_clone_rule.clicked.connect(self._clone_rule)
        self.btn_export_full.clicked.connect(lambda: self._export("full"))
        self.btn_export_clean.clicked.connect(lambda: self._export("cleaned"))
        self.btn_export_errors.clicked.connect(lambda: self._export("validation"))
        self.btn_export_dups.clicked.connect(lambda: self._export("duplicates"))
        self.btn_theme.clicked.connect(self._toggle_theme)

    def _load_default_rule(self) -> None:
        sample = resource_path("resources", "rules", "tbtp_masterlist.json")
        if not sample.exists():
            sample = Path(__file__).resolve().parents[2] / "resources" / "rules" / "tbtp_masterlist.json"
        if sample.exists():
            try:
                self._rule_set = RuleEngine.load(sample)
                self.rule_builder.load_rule_set(self._rule_set)
                self.start_row_spin.setValue(self._rule_set.header_row + 1)
                self.status.showMessage(f"Loaded rule: {self._rule_set.rule_name}")
            except Exception as exc:
                logger.warning("Could not load default rule: %s", exc)
                self.rule_builder._new_rule_set()
                self._rule_set = self.rule_builder.get_rule_set()
                self.start_row_spin.setValue(1)
        else:
            self.rule_builder._new_rule_set()
            self._rule_set = self.rule_builder.get_rule_set()
            self.start_row_spin.setValue(1)

    def _refresh_library(self) -> None:
        self.library_list.clear()
        for entry in self._rule_service.list_entries():
            self.library_list.addItem(
                f"{entry['rule_name']} — {entry['columns']} cols"
            )
            item = self.library_list.item(self.library_list.count() - 1)
            item.setData(256, entry["path"])  # Qt.UserRole

    def _on_library_selected(self) -> None:
        item = self.library_list.currentItem()
        if not item:
            return
        path = item.data(256)
        if path:
            try:
                self._rule_set = self._rule_service.load_from_library(path)
                self.rule_builder.load_rule_set(self._rule_set)
                self.start_row_spin.setValue(self._rule_set.header_row + 1)
                self.status.showMessage(f"Active rule: {self._rule_set.rule_name}")
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))

    def _on_rule_changed(self, rule_set: RuleSet) -> None:
        self._rule_set = rule_set

    def _browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Spreadsheet",
            "",
            "Spreadsheets (*.xlsx *.xls *.csv)",
        )
        if path:
            self._on_file_selected(path)

    def _on_file_selected(self, path: str) -> None:
        self._file_path = path
        self.file_drop.set_file(path)
        self.status.showMessage(f"File: {Path(path).name}")
        try:
            from sheetguard.services.file_loader import FileLoader

            df = FileLoader.load(path, self._rule_set)
            self.results_view.show_preview(df)
        except Exception as exc:
            QMessageBox.warning(self, "Preview", f"Could not preview file: {exc}")

    def _on_confirm_start_row(self) -> None:
        """Update the rule set header row and refresh preview if file is loaded."""
        user_row = self.start_row_spin.value()
        header_row = user_row - 1  # Convert 1-indexed to 0-indexed
        logger.info(f"Confirm start row clicked: user_row={user_row}, header_row={header_row}")
        
        if self._rule_set:
            self._rule_set.header_row = header_row
            logger.info(f"Rule set header_row updated to {header_row}")
        
        if self._file_path:
            logger.info(f"Loading file with new start row: {self._file_path}")
            self.btn_confirm_start_row.setEnabled(False)
            self.status.showMessage(f"Loading preview starting from row {user_row}...")
            try:
                from sheetguard.services.file_loader import FileLoader

                logger.info(f"FileLoader.load starting...")
                df = FileLoader.load(self._file_path, self._rule_set)
                logger.info(f"FileLoader.load completed: {len(df)} rows")
                self.results_view.show_preview(df)
                self.status.showMessage(f"Preview updated - data starts at row {user_row}, header at row {user_row - 1}")
                logger.info(f"Preview updated successfully")
            except Exception as exc:
                logger.exception(f"Error loading file: {exc}")
                QMessageBox.warning(self, "Preview", f"Could not preview file: {exc}")
            finally:
                self.btn_confirm_start_row.setEnabled(True)
        else:
            self.status.showMessage(f"Start row set to {user_row}. Load a file to preview.")

    def _run_processing(self) -> None:
        if not self._file_path:
            QMessageBox.warning(self, "Process", "Please select a file first.")
            return
        self._rule_set = self.rule_builder.get_rule_set()
        if not self._rule_set or not self._rule_set.columns:
            QMessageBox.warning(self, "Process", "Configure at least one column rule.")
            return
        try:
            RuleEngine.validate(self._rule_set)
        except Exception as exc:
            QMessageBox.critical(self, "Invalid Rules", str(exc))
            return

        self.btn_process.setEnabled(False)
        self.progress.setValue(0)
        self._worker = ProcessingWorker(self._rule_set, self._file_path)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    @Slot(int, str)
    def _on_progress(self, pct: int, msg: str) -> None:
        self.progress.setValue(pct)
        self.status.showMessage(msg)

    @Slot(object)
    def _on_finished(self, result: ProcessingResult) -> None:
        self._result = result
        self.results_view.show_result(result)
        self.btn_process.setEnabled(True)
        self.progress.setValue(100)
        self.status.showMessage(
            f"Done — {result.error_count} errors, {result.warning_count} warnings"
        )

    @Slot(str)
    def _on_failed(self, message: str) -> None:
        self.btn_process.setEnabled(True)
        QMessageBox.critical(self, "Processing Failed", message)

    def _import_rule(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import Rule", "", "JSON (*.json)")
        if path:
            try:
                rs = self._rule_service.import_file(path)
                self._rule_set = rs
                self.rule_builder.load_rule_set(rs)
                self.start_row_spin.setValue(rs.header_row + 1)
                self._refresh_library()
            except Exception as exc:
                QMessageBox.critical(self, "Import Error", str(exc))

    def _export_rule(self) -> None:
        rs = self.rule_builder.get_rule_set()
        if not rs:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Rule", "", "JSON (*.json)")
        if path:
            self._rule_service.export_file(rs, path)

    def _clone_rule(self) -> None:
        rs = self.rule_builder.get_rule_set()
        if not rs:
            return
        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "Clone", "New rule set name:")
        if ok and name:
            cloned = self._rule_service.clone(rs, name)
            self._rule_set = cloned
            self.rule_builder.load_rule_set(cloned)
            self.start_row_spin.setValue(cloned.header_row + 1)
            self._refresh_library()

    def _export(self, kind: str) -> None:
        if not self._result:
            QMessageBox.warning(self, "Export", "Run processing first.")
            return
        path = ""
        filters = "Excel (*.xlsx)"
        if kind == "full":
            path, _ = QFileDialog.getSaveFileName(
                self, "Export Full Report", "sheetguard_report.xlsx", filters
            )
            if path:
                WorkbookExporter().export_full_report(self._result, path)
        elif kind == "cleaned":
            path, _ = QFileDialog.getSaveFileName(
                self, "Export Cleaned Data", "sheetguard_cleaned.xlsx", filters
            )
            if path:
                WorkbookExporter().export_cleaned_only(self._result, path)
        elif kind == "validation":
            path, _ = QFileDialog.getSaveFileName(
                self, "Export Validation Report", "validation_report.xlsx", filters
            )
            if path:
                WorkbookExporter().export_validation_report(self._result, path)
        elif kind == "duplicates":
            path, _ = QFileDialog.getSaveFileName(
                self, "Export Duplicate Report", "duplicate_report.xlsx", filters
            )
            if path:
                dup_df = self.results_view._duplicates_df(self._result)
                WorkbookExporter().export_duplicate_report(self._result, dup_df, path)
        if path:
            self.status.showMessage(f"Exported: {path}")
            QMessageBox.information(self, "Export", f"Saved to {path}")

    def _toggle_theme(self) -> None:
        self._dark_mode = self.btn_theme.isChecked()
        app = QApplication.instance()
        if isinstance(app, QApplication):
            apply_theme(app, self._dark_mode)


def run_app() -> None:
    """Application entry point for GUI."""
    import sys

    from sheetguard.utils.logging_config import setup_logging

    setup_logging()
    app = QApplication(sys.argv)
    apply_theme(app, dark=True)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
