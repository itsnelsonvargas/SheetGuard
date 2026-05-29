"""Main application window."""

from __future__ import annotations

from html import escape
import logging
from pathlib import Path
from urllib.parse import quote

from PySide6.QtCore import QThread, Signal, Slot, Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
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
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from sheetguard.core.exporter import WorkbookExporter
from sheetguard.core.rule_engine import RuleEngine
from sheetguard.gui.results_view import ResultsView
from sheetguard.gui.bug_report_dialog import BugReportDialog
from sheetguard.gui.rule_builder import RuleBuilderPanel
from sheetguard.gui.theme import apply_theme
from sheetguard.gui.widgets.file_drop import FileDropZone
from sheetguard.gui.widgets.processing_overlay import ProcessingOverlay
from sheetguard.models.results import ProcessingResult
from sheetguard.models.rules import RuleSet
from sheetguard.services.pipeline import ProcessingPipeline
from sheetguard.services.rule_service import RuleService
from sheetguard.utils.column_utils import coerce_cell, resolve_column_name
from sheetguard.utils.paths import resource_path

logger = logging.getLogger(__name__)


class StartRowDialog(QDialog):
    """Dialog to select which row data should start from."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select Data Start Row")
        self.setMinimumWidth(350)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Which row should data start from?"))
        layout.addWidget(QLabel("(1 = first row, 2 = second row, etc.)"))

        row_layout = QHBoxLayout()
        row_layout.addWidget(QLabel("Start Row:"))
        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(1)
        self.spinbox.setMaximum(9999)
        self.spinbox.setValue(1)
        self.spinbox.setMinimumWidth(100)
        row_layout.addWidget(self.spinbox)
        row_layout.addStretch()
        layout.addLayout(row_layout)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Load File")
        btn_cancel = QPushButton("Cancel")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def get_start_row(self) -> int:
        """Return the selected start row (1-indexed)."""
        return self.spinbox.value()


class HelpDialog(QDialog):
    """In-app guide for common SheetGuard workflows and terms."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("How to Use SheetGuard")
        self.setMinimumSize(620, 620)
        self.setModal(True)

        layout = QVBoxLayout(self)

        guide = QTextBrowser()
        guide.setOpenExternalLinks(False)
        guide.setHtml(
            """
            <h1>How to Use SheetGuard</h1>

            <h2>Basic workflow</h2>
            <ol>
              <li><b>Choose a rule</b> from the Rule Library, or build one in Rule Builder.</li>
              <li><b>Upload a spreadsheet</b> using Browse File or drag and drop.</li>
              <li><b>Select the Start Row</b> when prompted so SheetGuard reads the right headers.</li>
              <li><b>Run Clean &amp; Validate</b> to clean data and find issues.</li>
              <li><b>Review the results</b>, then export the report you need.</li>
            </ol>

            <h2>Terms used in the app</h2>
            <p><b>Rule Library</b> - saved rule sets you can select, import, export, clone, or delete.</p>
            <p><b>Rule Set</b> - a named collection of column rules and duplicate check rules.</p>
            <p><b>Rule Builder</b> - the panel where you create or edit the active rule set.</p>
            <p><b>Columns</b> - the spreadsheet fields SheetGuard should clean or validate.</p>
            <p><b>Column Rule</b> - settings for one column, such as required, email check, allowed values, regex, or lookup.</p>
            <p><b>Cleaning</b> - automatic fixes applied before validation, such as trimming spaces, changing case, or normalizing dates.</p>
            <p><b>Validation Rules</b> - checks that flag data problems after cleaning.</p>
            <p><b>Required</b> - marks a column as mandatory. Empty cells are reported.</p>
            <p><b>Warning Only</b> - reports issues as warnings instead of errors.</p>
            <p><b>Error</b> - a data issue that should usually be fixed before using the file.</p>
            <p><b>Warning</b> - a suspicious value that may need review but may still be acceptable.</p>
            <p><b>Lookup Table</b> - a reference list used to check whether values are valid.</p>
            <p><b>Duplicate Check Rules</b> - column combinations used to detect repeated records.</p>
            <p><b>AI Review</b> - an optional review that summarizes possible data quality issues.</p>
            <p><b>Export Full Report</b> - saves cleaned data, validation findings, and duplicate findings together.</p>
            <p><b>Export Cleaned Data</b> - saves only the cleaned spreadsheet data.</p>
            <p><b>Export Validation Report</b> - saves only validation errors and warnings.</p>
            <p><b>Export Duplicate Report</b> - saves duplicate groups found by duplicate check rules.</p>
            """
        )
        layout.addWidget(guide)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


class RulePreviewDialog(QDialog):
    """Show a sample run of the active rules before full processing."""

    navigate_requested = Signal(int, str)
    run_requested = Signal()

    def __init__(self, html: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Rule Test Preview")
        self.setMinimumSize(760, 640)
        self.setModal(True)
        self.ran_full_clean = False

        layout = QVBoxLayout(self)

        preview = QTextBrowser()
        preview.setOpenExternalLinks(False)
        preview.setOpenLinks(False)
        preview.anchorClicked.connect(self._on_anchor_clicked)
        preview.setHtml(html)
        layout.addWidget(preview)

        btn_row = QHBoxLayout()
        btn_run = QPushButton("Run Full Clean")
        btn_run.clicked.connect(self._request_run)
        btn_row.addWidget(btn_run)

        btn_close = QPushButton("Close")
        btn_close.setObjectName("secondary")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _on_anchor_clicked(self, url) -> None:
        if url.scheme() != "preview-row":
            return
        payload = url.path()
        try:
            row_text, column_name = payload.split("|", 1)
            row_index = int(row_text)
        except (ValueError, TypeError):
            return
        if column_name:
            self.navigate_requested.emit(row_index, column_name)

    def _request_run(self) -> None:
        self.ran_full_clean = True
        self.run_requested.emit()
        self.accept()


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


class AIWorker(QThread):
    """Background thread for AI review."""

    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, df) -> None:
        super().__init__()
        self.df = df

    def run(self) -> None:
        try:
            from sheetguard.services.ai_reviewer import AIReviewService
            service = AIReviewService()
            insights = service.review_data(self.df)
            self.finished_ok.emit(insights)
        except Exception as exc:
            logger.exception("AI Review failed")
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    """Primary SheetGuard window with sidebar layout."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SheetGuard")

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
        sidebar_scroll.setMinimumWidth(400)
        sidebar_scroll.setMaximumWidth(500)
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sidebar_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        sidebar_scroll.setFrameShape(QFrame.NoFrame)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(15)

        sidebar_layout.addWidget(QLabel("FILE UPLOAD"))
        self.file_drop = FileDropZone()
        self.file_drop.file_selected.connect(self._on_file_selected)
        sidebar_layout.addWidget(self.file_drop)

        file_btns = QHBoxLayout()
        btn_browse = QPushButton("📂 Browse File...")
        btn_browse.setObjectName("secondary")
        btn_browse.clicked.connect(self._browse_file)
        file_btns.addWidget(btn_browse)

        self.btn_ai_review = QPushButton("🤖 AI Review")
        self.btn_ai_review.setObjectName("success")
        self.btn_ai_review.clicked.connect(self._run_ai_review)
        file_btns.addWidget(self.btn_ai_review)

        sidebar_layout.addLayout(file_btns)

        sidebar_layout.addWidget(QLabel("RULE LIBRARY"))
        self.library_list = QListWidget()
        self.library_list.setObjectName("ruleLibrary")
        self.library_list.setMinimumHeight(150)
        self.library_list.currentItemChanged.connect(self._on_library_selected)
        sidebar_layout.addWidget(self.library_list)

        # Split library buttons into two rows to save horizontal space
        lib_btns_row1 = QHBoxLayout()
        self.btn_import_rule = QPushButton("📥 Import")
        self.btn_export_rule = QPushButton("📤 Export")
        lib_btns_row1.addWidget(self.btn_import_rule)
        lib_btns_row1.addWidget(self.btn_export_rule)
        sidebar_layout.addLayout(lib_btns_row1)

        lib_btns_row2 = QHBoxLayout()
        self.btn_clone_rule = QPushButton("📋 Clone")
        self.btn_delete_rule = QPushButton("🗑️ Delete")
        self.btn_delete_rule.setObjectName("danger")
        lib_btns_row2.addWidget(self.btn_clone_rule)
        lib_btns_row2.addWidget(self.btn_delete_rule)
        sidebar_layout.addLayout(lib_btns_row2)

        self.rule_builder = RuleBuilderPanel()
        self.rule_builder.rule_changed.connect(self._on_rule_changed)
        self.rule_builder.rule_saved.connect(self._refresh_library)
        sidebar_layout.addWidget(self.rule_builder)

        sidebar_layout.addWidget(QLabel("PROCESSING"))
        self.btn_preview_rules = QPushButton("Preview Rule Test")
        self.btn_preview_rules.setObjectName("secondary")
        self.btn_preview_rules.setToolTip("Test the active rules on the first 25 rows")
        sidebar_layout.addWidget(self.btn_preview_rules)

        self.btn_process = QPushButton("⚡ Run Clean & Validate")
        self.btn_process.setMinimumHeight(45)
        sidebar_layout.addWidget(self.btn_process)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%p %")
        self.progress.setTextVisible(True)
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress.setFixedHeight(24)
        sidebar_layout.addWidget(self.progress)

        sidebar_layout.addWidget(QLabel("EXPORT REPORTS"))
        self.btn_export_full = QPushButton("📊 Export Full Report")
        self.btn_export_clean = QPushButton("🧹 Export Cleaned Data")
        self.btn_export_errors = QPushButton("⚠️ Export Validation Report")
        self.btn_export_dups = QPushButton("👯 Export Duplicate Report")
        for b in (
            self.btn_export_full,
            self.btn_export_clean,
            self.btn_export_errors,
            self.btn_export_dups,
        ):
            sidebar_layout.addWidget(b)

        sidebar_layout.addSpacing(10)
        self.btn_help = QPushButton("How to Use")
        self.btn_help.setObjectName("secondary")
        self.btn_help.setToolTip("Learn the workflow and app terms")
        sidebar_layout.addWidget(self.btn_help)

        self.btn_theme = QPushButton("🌙 Dark Mode" if self._dark_mode else "☀️ Light Mode")
        self.btn_theme.setObjectName("theme_toggle")
        self.btn_theme.setCheckable(True)
        self.btn_theme.setChecked(self._dark_mode)
        sidebar_layout.addWidget(self.btn_theme)
        
        sidebar_layout.addStretch()

        self.btn_bug = QPushButton("🐞  Submit a Bug Report")
        self.btn_bug.setObjectName("bug_link")
        self.btn_bug.clicked.connect(self._open_bug_report)
        sidebar_layout.addWidget(self.btn_bug)

        sidebar_scroll.setWidget(sidebar)
        splitter.addWidget(sidebar_scroll)

        self.results_view = ResultsView()
        self.results_view.request_row_deletion.connect(self._on_row_deleted)
        splitter.addWidget(self.results_view)
        splitter.setStretchFactor(1, 1)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

        self.processing_overlay = ProcessingOverlay(self)

        self.btn_preview_rules.clicked.connect(self._preview_rule_test)
        self.btn_process.clicked.connect(self._run_processing)
        self.btn_import_rule.clicked.connect(self._import_rule)
        self.btn_export_rule.clicked.connect(self._export_rule)
        self.btn_clone_rule.clicked.connect(self._clone_rule)
        self.btn_delete_rule.clicked.connect(self._delete_rule)
        self.btn_export_full.clicked.connect(lambda: self._export("full"))
        self.btn_export_clean.clicked.connect(lambda: self._export("cleaned"))
        self.btn_export_errors.clicked.connect(lambda: self._export("validation"))
        self.btn_export_dups.clicked.connect(lambda: self._export("duplicates"))
        self.btn_help.clicked.connect(self._open_help)
        self.btn_theme.clicked.connect(self._toggle_theme)

    def _load_default_rule(self) -> None:
        sample = resource_path("resources", "rules", "tbtp_masterlist.json")
        if not sample.exists():
            sample = Path(__file__).resolve().parents[2] / "resources" / "rules" / "tbtp_masterlist.json"
        if sample.exists():
            try:
                self._rule_set = RuleEngine.load(sample)
                self.rule_builder.load_rule_set(self._rule_set)
                self.status.showMessage(f"Loaded rule: {self._rule_set.rule_name}")
            except Exception as exc:
                logger.warning("Could not load default rule: %s", exc)
                self.rule_builder._new_rule_set()
                self._rule_set = self.rule_builder.get_rule_set()
        else:
            self.rule_builder._new_rule_set()
            self._rule_set = self.rule_builder.get_rule_set()

    def _refresh_library(self) -> None:
        selected_path = None
        current_item = self.library_list.currentItem()
        if current_item:
            selected_path = current_item.data(256)

        self.library_list.clear()
        for entry in self._rule_service.list_entries():
            self.library_list.addItem(
                f"{entry['rule_name']} (v{entry['version']}) — {entry['columns']} cols"
            )
            item = self.library_list.item(self.library_list.count() - 1)
            item.setData(256, entry["path"])
            if selected_path and entry["path"] == selected_path:
                self.library_list.setCurrentItem(item)

    def _on_library_selected(self) -> None:
        item = self.library_list.currentItem()
        if not item:
            return
        path = item.data(256)
        if path:
            try:
                self._rule_set = self._rule_service.load_from_library(path)
                self.rule_builder.load_rule_set(self._rule_set)
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
        
        # Ask user which row to start from
        dialog = StartRowDialog(self)
        if dialog.exec() != QDialog.Accepted:
            self._file_path = None
            self.file_drop.clear()
            return
        
        start_row = dialog.get_start_row()
        header_row = start_row - 1  # Convert to 0-indexed
        
        if self._rule_set:
            self._rule_set.header_row = header_row
        
        self.status.showMessage(f"File: {Path(path).name} (data starts at row {start_row})")
        try:
            from sheetguard.services.file_loader import FileLoader

            df = FileLoader.load(path, self._rule_set)
            self.results_view.show_preview(df, self._rule_set)
        except Exception as exc:
            QMessageBox.warning(self, "Preview", f"Could not preview file: {exc}")

    def _run_ai_review(self) -> None:
        if not self._file_path:
            QMessageBox.warning(self, "AI Review", "Please select a file first.")
            return
            
        try:
            from sheetguard.services.file_loader import FileLoader
            df = FileLoader.load(self._file_path, self._rule_set)
        except Exception as exc:
            QMessageBox.warning(self, "AI Review", f"Could not load file: {exc}")
            return
            
        self.btn_ai_review.setEnabled(False)
        self.btn_ai_review.setText("🤖 Reviewing...")
        self.processing_overlay.show_processing("AI Data Review")
        self.status.showMessage("AI is reviewing data...")
        
        self._ai_worker = AIWorker(df)
        self._ai_worker.finished_ok.connect(self._on_ai_finished)
        self._ai_worker.failed.connect(self._on_ai_failed)
        self._ai_worker.start()

    @Slot(str)
    def _on_ai_finished(self, insights: str) -> None:
        self.btn_ai_review.setEnabled(True)
        self.btn_ai_review.setText("🤖 AI Review")
        self.processing_overlay.hide()
        self.status.showMessage("AI Review complete.")
        
        from sheetguard.gui.ai_insights_dialog import AIInsightsDialog
        dlg = AIInsightsDialog(insights, self)
        dlg.exec()

    @Slot(str)
    def _on_ai_failed(self, message: str) -> None:
        self.btn_ai_review.setEnabled(True)
        self.btn_ai_review.setText("🤖 AI Review")
        self.processing_overlay.hide()
        QMessageBox.critical(self, "AI Review Failed", f"AI Review failed:\n{message}")
        self.status.showMessage("AI Review failed.")

    def _preview_rule_test(self) -> None:
        if not self._file_path:
            QMessageBox.warning(self, "Preview Rule Test", "Please select a file first.")
            return

        self._rule_set = self.rule_builder.get_rule_set()
        if not self._rule_set or not self._rule_set.columns:
            QMessageBox.warning(
                self,
                "Preview Rule Test",
                "Configure at least one column rule before previewing.",
            )
            return

        try:
            RuleEngine.validate(self._rule_set)
        except Exception as exc:
            QMessageBox.critical(self, "Invalid Rules", str(exc))
            return

        try:
            from sheetguard.services.file_loader import FileLoader

            sample_size = 25
            source_df = FileLoader.load(self._file_path, self._rule_set)
            sample_df = source_df.head(sample_size).copy()
            if sample_df.empty:
                QMessageBox.warning(self, "Preview Rule Test", "The selected file has no rows to preview.")
                return

            result = ProcessingPipeline(self._rule_set).run(sample_df)
            html = self._build_rule_preview_html(result, len(source_df), sample_size)
            dlg = RulePreviewDialog(html, self)
            dlg.navigate_requested.connect(self._focus_preview_cell)
            dlg.run_requested.connect(self._run_processing)
            dlg.exec()
            if not dlg.ran_full_clean:
                self.status.showMessage("Rule test preview complete.")
        except Exception as exc:
            logger.exception("Rule test preview failed")
            QMessageBox.critical(self, "Preview Rule Test Failed", str(exc))

    def _build_rule_preview_html(
        self,
        result: ProcessingResult,
        total_rows: int,
        requested_sample_size: int,
    ) -> str:
        sample_rows = len(result.cleaned_df)
        change_rows = self._cleaning_preview_rows(result)
        issue_rows = self._validation_preview_rows(result)
        duplicate_rows = [dup.to_dict() for dup in result.duplicates]

        return f"""
        <style>
          body {{ font-family: "Segoe UI", sans-serif; }}
          h1 {{ margin-bottom: 4px; }}
          h2 {{ margin-top: 22px; }}
          table {{ border-collapse: collapse; width: 100%; margin-top: 8px; }}
          th, td {{ border: 1px solid #CBD5E1; padding: 6px 8px; vertical-align: top; }}
          th {{ background: #E2E8F0; color: #0F172A; }}
          .ok {{ color: #059669; font-weight: 700; }}
          .warn {{ color: #D97706; font-weight: 700; }}
          .err {{ color: #DC2626; font-weight: 700; }}
          .muted {{ color: #64748B; }}
        </style>

        <h1>Rule Test Preview</h1>
        <p class="muted">
          Tested <b>{sample_rows}</b> of <b>{total_rows}</b> rows using
          <b>{escape(result.rule_set.rule_name if result.rule_set else "Active Rule Set")}</b>.
          This preview uses up to the first {requested_sample_size} data rows and does not change the full results.
        </p>

        <h2>Summary</h2>
        <table>
          <tr><th>Check</th><th>Result</th></tr>
          <tr><td>Cells that would be cleaned</td><td>{len(change_rows)}</td></tr>
          <tr><td>Validation errors</td><td class="err">{result.error_count}</td></tr>
          <tr><td>Validation warnings</td><td class="warn">{result.warning_count}</td></tr>
          <tr><td>Duplicate groups</td><td>{len(result.duplicates)}</td></tr>
        </table>

        <h2>This Column Will Be Cleaned Like This</h2>
        {self._html_table(change_rows, ["row", "column_rule", "triggered_rule", "column", "original_value", "cleaned_value"], "No cleaning changes found in the preview rows.")}

        <h2>These Validations Will Fail</h2>
        {self._html_table(issue_rows, ["view", "row", "column_rule", "triggered_rule", "column", "severity", "message", "cleaned_value"], "No validation failures found in the preview rows.")}

        <h2>Duplicate Check Preview</h2>
        {self._html_table(duplicate_rows, ["rule_name", "key", "rows", "count"], "No duplicate groups found in the preview rows.")}
        """

    def _cleaning_preview_rows(self, result: ProcessingResult) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        rule_by_column = self._rule_by_resolved_column(result)
        for row_idx in range(len(result.cleaned_df)):
            for column in result.cleaned_df.columns:
                original = coerce_cell(result.original_df.iloc[row_idx][column])
                cleaned = coerce_cell(result.cleaned_df.iloc[row_idx][column])
                if str(original) == str(cleaned):
                    continue
                rule = rule_by_column.get(str(column))
                rows.append(
                    {
                        "row": row_idx + 1,
                        "column_rule": rule.field_id if rule else column,
                        "triggered_rule": ", ".join(rule.cleaning) if rule else "cleaning",
                        "column": column,
                        "original_value": original,
                        "cleaned_value": cleaned,
                    }
                )
        return rows

    def _validation_preview_rows(self, result: ProcessingResult) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for issue in result.issues:
            rows.append(
                {
                    "view": (
                        f'<a href="preview-row:{issue.row_index}|{quote(issue.column, safe="")}">'
                        "View row</a>"
                    ),
                    "row": issue.row_index + 1,
                    "column_rule": issue.field_id,
                    "triggered_rule": issue.rule_type,
                    "column": issue.column,
                    "severity": issue.severity,
                    "message": issue.message,
                    "cleaned_value": issue.cleaned_value,
                }
            )
        return rows

    @staticmethod
    def _rule_by_resolved_column(result: ProcessingResult) -> dict[str, object]:
        mapping: dict[str, object] = {}
        if not result.rule_set:
            return mapping
        for rule in result.rule_set.columns:
            try:
                mapping[resolve_column_name(result.cleaned_df, rule.column)] = rule
            except (KeyError, ValueError):
                continue
        return mapping

    def _focus_preview_cell(self, row_index: int, column_name: str) -> None:
        if self.results_view.focus_preview_cell(row_index, column_name):
            self.status.showMessage(f"Focused preview row {row_index + 1}, column {column_name}")
        else:
            self.status.showMessage(f"Could not find row {row_index + 1}, column {column_name} in preview")

    @staticmethod
    def _html_table(rows: list[dict[str, object]], columns: list[str], empty_text: str) -> str:
        if not rows:
            return f'<p class="ok">{escape(empty_text)}</p>'

        limited_rows = rows[:100]
        header = "".join(f"<th>{escape(col.replace('_', ' ').title())}</th>" for col in columns)
        body = []
        for row in limited_rows:
            cells = []
            for col in columns:
                value = row.get(col, "")
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                if col == "view":
                    cells.append(f"<td>{value}</td>")
                else:
                    cells.append(f"<td>{escape(str(value))}</td>")
            body.append(f"<tr>{''.join(cells)}</tr>")

        note = ""
        if len(rows) > len(limited_rows):
            note = f"<p class=\"muted\">Showing first {len(limited_rows)} of {len(rows)} rows.</p>"
        return f"<table><tr>{header}</tr>{''.join(body)}</table>{note}"

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
        self.processing_overlay.show_processing("Cleaning & Validating")
        self._worker = ProcessingWorker(self._rule_set, self._file_path)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    @Slot(int, str)
    def _on_progress(self, pct: int, msg: str) -> None:
        self.progress.setValue(pct)
        self.processing_overlay.update_progress(pct, msg)
        self.status.showMessage(msg)

    @Slot(object)
    def _on_finished(self, result: ProcessingResult) -> None:
        self._result = result
        self.results_view.show_result(result)
        self.btn_process.setEnabled(True)
        self.progress.setValue(100)
        self.processing_overlay.hide()
        self.status.showMessage(
            f"Done — {result.error_count} errors, {result.warning_count} warnings"
        )

    @Slot(str)
    def _on_failed(self, message: str) -> None:
        self.btn_process.setEnabled(True)
        self.processing_overlay.hide()
        QMessageBox.critical(self, "Processing Failed", message)

    @Slot(int)
    def _on_row_deleted(self, row_idx: int) -> None:
        if not self._result:
            return
        
        # Confirm deletion
        ans = QMessageBox.question(
            self, 
            "Delete Row", 
            f"Are you sure you want to delete row {row_idx + 1} from the results?"
        )
        if ans == QMessageBox.StandardButton.Yes:
            try:
                self._result.drop_row(row_idx)
                self.results_view.show_result(self._result)
                self.status.showMessage(f"Deleted row {row_idx + 1}")
            except Exception as exc:
                QMessageBox.critical(self, "Delete Error", str(exc))

    def _import_rule(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import Rule", "", "JSON (*.json)")
        if path:
            try:
                rs = self._rule_service.import_file(path)
                self._rule_set = rs
                self.rule_builder.load_rule_set(rs)
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
            self._refresh_library()

    def _delete_rule(self) -> None:
        item = self.library_list.currentItem()
        if not item:
            return
        path = item.data(256)
        if not path:
            return
        name = item.text().split("(")[0].strip()
        ans = QMessageBox.question(
            self, "Delete Rule", f"Are you sure you want to delete '{name}'?"
        )
        if ans == QMessageBox.StandardButton.Yes:
            self._rule_service.delete(path)
            self._refresh_library()
            self.status.showMessage(f"Deleted rule: {name}")

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
        self.btn_theme.setText("🌙 Dark Mode" if self._dark_mode else "☀️ Light Mode")
        app = QApplication.instance()
        if isinstance(app, QApplication):
            apply_theme(app, self._dark_mode)

    def _open_bug_report(self) -> None:
        """Open the bug report dialog."""
        dlg = BugReportDialog(self)
        dlg.exec()

    def _open_help(self) -> None:
        """Open the in-app usage guide."""
        dlg = HelpDialog(self)
        dlg.exec()


def run_app() -> None:
    """Application entry point for SheetGuard."""
    import sys

    from sheetguard.utils.logging_config import setup_logging

    setup_logging()
    app = QApplication(sys.argv)
    apply_theme(app, dark=True)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
