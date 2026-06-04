"""Main application window."""

from __future__ import annotations

import random
from html import escape
import logging
from pathlib import Path
from urllib.parse import quote
from string import ascii_lowercase

from PySide6.QtCore import QThread, Signal, Slot, Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QColor
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
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QLineEdit,
    QSizePolicy,
)

from sheetguard.core.exporter import WorkbookExporter
from sheetguard.gui.lookup_manager_dialog import LookupTableManagerDialog
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
        btn_ok = QPushButton("📂 Load File")
        btn_cancel = QPushButton("✖ Cancel")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def get_start_row(self) -> int:
        """Return the selected start row (1-indexed)."""
        return self.spinbox.value()


class MainWindow(QMainWindow):
    """SheetGuard Ultra window with high-fidelity sidebars."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SheetGuard Ultra")

        self._rule_service = RuleService()
        self._rule_set: RuleSet | None = None
        self._file_path: str | None = None
        self._source_df = None
        self._result: ProcessingResult | None = None
        self._worker: ProcessingWorker | None = None
        self._load_worker: FileLoadWorker | None = None
        self._dark_mode = True

        self._build_ui()
        self._load_default_rule()
        self._refresh_library()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- 0. BRANDING HEADER ---
        brand_bar = QFrame()
        brand_bar.setObjectName("brandBar")
        brand_bar.setStyleSheet("background-color: #0B0E14; border-bottom: 1px solid #1E242E;")
        brand_bar_layout = QHBoxLayout(brand_bar)
        brand_bar_layout.setContentsMargins(15, 10, 15, 10)
        
        lbl_shield = QLabel("🛡️")
        lbl_shield.setObjectName("brandIcon")
        brand_bar_layout.addWidget(lbl_shield)
        
        lbl_title = QLabel("SheetGuard Ultra")
        lbl_title.setObjectName("brandTitle")
        brand_bar_layout.addWidget(lbl_title)
        brand_bar_layout.addStretch()
        
        root_layout.addWidget(brand_bar)

        # Main Workspace Container (Horizontal)
        workspace_container = QWidget()
        workspace_layout = QHBoxLayout(workspace_container)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)
        root_layout.addWidget(workspace_container, stretch=1)

        # --- 1. ICON SIDEBAR (FAR LEFT) ---
        icon_sidebar = QFrame()
        icon_sidebar.setObjectName("iconSidebar")
        icon_sidebar.setFixedWidth(35)
        icon_sidebar_layout = QVBoxLayout(icon_sidebar)
        icon_sidebar_layout.setContentsMargins(0, 5, 0, 15)
        icon_sidebar_layout.setSpacing(5)
        icon_sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        # Navigation Icons
        btn_menu = self._create_nav_icon("☰")
        btn_file_ops = self._create_nav_icon("📄") 
        btn_file_ops.setProperty("active", "true")
        btn_db = self._create_nav_icon("🗄️") 
        btn_settings_top = self._create_nav_icon("⚙️") 
        
        for b in (btn_menu, btn_file_ops, btn_db, btn_settings_top):
            icon_sidebar_layout.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        icon_sidebar_layout.addStretch()
        
        # Bottom Icons
        btn_bug_nav = self._create_nav_icon("🐞")
        btn_help_nav = self._create_nav_icon("❓")
        btn_settings_bot = self._create_nav_icon("⚙️")

        for b in (btn_bug_nav,btn_help_nav, btn_settings_bot, btn_settings_bot):
            icon_sidebar_layout.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)
            # Connect bug report dialog
            btn_bug_nav.clicked.connect(self._open_bug_report)

        workspace_layout.addWidget(icon_sidebar)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        workspace_layout.addWidget(self.main_splitter)

        # --- 2. COMMAND CENTER (MIDDLE SIDEBAR) ---
        sidebar_pane = QFrame()
        sidebar_pane.setObjectName("sidebar")
        sidebar_pane.setMinimumWidth(300)
        sidebar_main_layout = QVBoxLayout(sidebar_pane)
        sidebar_main_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_main_layout.setSpacing(0)

        # Fixed Sub-Header
        header_pane = QFrame()
        header_layout = QHBoxLayout(header_pane)
        header_layout.setContentsMargins(15, 15, 15, 10)
        header_text = QLabel("Command Center")
        header_text.setStyleSheet("font-size: 15px; font-weight: 800; color: #E2E8F0;")
        header_collapse = QLabel("«")
        header_collapse.setStyleSheet("color: #475569; font-weight: bold;")
        header_layout.addWidget(header_text)
        header_layout.addStretch()
        header_layout.addWidget(header_collapse)
        sidebar_main_layout.addWidget(header_pane)

        # Scrollable Content Area
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setObjectName("sidebarScroll")
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        sidebar_content = QFrame()
        sidebar_content.setObjectName("sidebarContent")
        sidebar_layout = QVBoxLayout(sidebar_content)
        sidebar_layout.setContentsMargins(15, 0, 15, 10)
        sidebar_layout.setSpacing(12)

        # FILE OPS
        lbl_file_ops = QLabel("FILE OPS")
        lbl_file_ops.setObjectName("groupHeader")
        sidebar_layout.addWidget(lbl_file_ops)

        self.btn_browse = QPushButton("  📁 Browse")
        self.btn_browse.setObjectName("browseAction")
        self.btn_browse.setMinimumHeight(40)
        self.btn_browse.clicked.connect(self._browse_file)
        sidebar_layout.addWidget(self.btn_browse)

        self.btn_import_api = QPushButton("  ↑ Import API")
        self.btn_import_api.setObjectName("actionSecondary")
        self.btn_import_api.setMinimumHeight(34)
        sidebar_layout.addWidget(self.btn_import_api)

        # Styled Drop Zone
        self.file_drop = FileDropZone()
        self.file_drop.setObjectName("dropZone")
        self.file_drop.setMinimumHeight(85)
        self.file_drop.file_selected.connect(self._on_file_selected)
        sidebar_layout.addWidget(self.file_drop)

        # AI CORE
        lbl_ai_core = QLabel("AI CORE")
        lbl_ai_core.setObjectName("groupHeader")
        sidebar_layout.addWidget(lbl_ai_core)

        self.btn_model_select = QPushButton("  🌐 Model Select")
        self.btn_model_select.setObjectName("actionSecondary")
        self.btn_prompt_builder = QPushButton("  💬 Prompt Builder")
        self.btn_prompt_builder.setObjectName("actionSecondary")
        for b in (self.btn_model_select, self.btn_prompt_builder):
            b.setMinimumHeight(34)
            sidebar_layout.addWidget(b)

        # RULE LIBRARY
        lbl_rule_lib = QLabel("RULE LIBRARY")
        lbl_rule_lib.setObjectName("groupHeader")
        sidebar_layout.addWidget(lbl_rule_lib)

        lib_search_layout = QHBoxLayout()
        self.search_library = QLineEdit()
        self.search_library.setPlaceholderText("Advanced filtering")
        self.search_library.setMinimumHeight(32)
        lib_search_layout.addWidget(self.search_library)
        lbl_filter_icon = QLabel("▽")
        lbl_filter_icon.setStyleSheet("color: #94A3B8;")
        lib_search_layout.addWidget(lbl_filter_icon)
        sidebar_layout.addLayout(lib_search_layout)
        self.search_library.textChanged.connect(self._filter_library)

        lbl_rule_builder = QLabel("Visual Rule Builder")
        lbl_rule_builder.setStyleSheet("color: #E2E8F0; font-weight: 600; font-size: 12px; margin-top: 5px;")
        sidebar_layout.addWidget(lbl_rule_builder)

        self.library_list = QTreeWidget()
        self.library_list.setObjectName("ruleLibrary")
        self.library_list.setMinimumHeight(280)
        self.library_list.setHeaderHidden(True)
        self.library_list.itemClicked.connect(self._on_library_selected)
        sidebar_layout.addWidget(self.library_list)

        sidebar_layout.addStretch()

        sidebar_scroll.setWidget(sidebar_content)
        sidebar_main_layout.addWidget(sidebar_scroll)

        # Fixed Bottom Action Buttons
        bottom_pane = QFrame()
        bottom_pane.setObjectName("sidebarBottom")
        bottom_layout = QHBoxLayout(bottom_pane)
        bottom_layout.setContentsMargins(15, 12, 15, 15)
        bottom_layout.setSpacing(10)

        self.btn_clone_rule = QPushButton("  📋 Clone")
        self.btn_clone_rule.setObjectName("actionSecondary")
        self.btn_clone_rule.setMinimumHeight(36)
        
        self.btn_delete_rule = QPushButton("  🗑️ Delete")
        self.btn_delete_rule.setObjectName("deleteAction")
        self.btn_delete_rule.setMinimumHeight(36)
        
        bottom_layout.addWidget(self.btn_clone_rule)
        bottom_layout.addWidget(self.btn_delete_rule)
        sidebar_main_layout.addWidget(bottom_pane)

        self.main_splitter.addWidget(sidebar_pane)

        # --- 3. LIVE WORKSPACE (CENTER) ---
        workspace = QWidget()
        workspace_layout_ws = QVBoxLayout(workspace)
        workspace_layout_ws.setContentsMargins(20, 20, 20, 10)
        workspace_layout_ws.setSpacing(0)

        ws_header_layout = QHBoxLayout()
        ws_header = QLabel("Live Workspace")
        ws_header.setStyleSheet("font-size: 18px; font-weight: 700; color: #E2E8F0;")
        ws_header_layout.addWidget(ws_header)
        ws_header_layout.addStretch()
        
        # Top Progress Bar (Horizontal)
        self.top_progress = QProgressBar()
        self.top_progress.setFixedWidth(200)
        self.top_progress.setFixedHeight(12)
        self.top_progress.setFormat("")
        workspace_layout_ws.addLayout(ws_header_layout)
        ws_header_layout.addWidget(self.top_progress)
        ws_header_layout.addWidget(QLabel("100%"))

        # Main Results View (Contains its own dashboard and search)
        self.results_view = ResultsView()
        self.results_view.request_row_deletion.connect(self._on_row_deleted)
        workspace_layout_ws.addWidget(self.results_view)

        self.main_splitter.addWidget(workspace)

        # --- 4. ACTION & ANALYTICS (RIGHT) ---
        right_pane = QFrame()
        right_pane.setObjectName("sidebar")
        right_pane.setMinimumWidth(320)
        right_pane.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        
        right_layout = QVBoxLayout(right_pane)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(12)

        header_right = QLabel("Action & Analytics")
        header_right.setStyleSheet("font-size: 16px; font-weight: 700; color: #E2E8F0; margin-bottom: 5px;")
        header_right.setWordWrap(True)
        right_layout.addWidget(header_right)

        lbl_rule_details = QLabel("RULE DETAILS")
        lbl_rule_details.setWordWrap(True)
        right_layout.addWidget(lbl_rule_details)
        
        self.rule_builder = RuleBuilderPanel()
        self.rule_builder.rule_changed.connect(self._on_rule_changed)
        self.rule_builder.rule_saved.connect(self._refresh_library)
        self.rule_builder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout.addWidget(self.rule_builder, stretch=1)

        lbl_visual_summary = QLabel("VISUAL SUMMARY")
        lbl_visual_summary.setWordWrap(True)
        right_layout.addWidget(lbl_visual_summary)
        
        self.progress = QProgressBar()
        self.progress.setFormat("Processing %p%")
        self.progress.setMinimumHeight(16)
        self.progress.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        right_layout.addWidget(self.progress)
        
        self.btn_process = QPushButton("⚡ Run Clean & Validate")
        self.btn_process.setObjectName("primary")
        self.btn_process.setMinimumHeight(38)
        self.btn_process.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_process.clicked.connect(self._run_processing)
        right_layout.addWidget(self.btn_process)

        lbl_export = QLabel("EXPORT")
        lbl_export.setWordWrap(True)
        right_layout.addWidget(lbl_export)
        
        export_layout = QHBoxLayout()
        export_layout.setSpacing(10)
        self.btn_export_full = QPushButton("↑ Export Full")
        self.btn_export_full.setObjectName("primary")
        self.btn_export_clean = QPushButton("Export Clean")
        self.btn_export_clean.setObjectName("actionSecondary")
        for b in (self.btn_export_full, self.btn_export_clean):
            b.setMinimumHeight(34)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            export_layout.addWidget(b, stretch=1)
        export_layout.setStretchFactor(self.btn_export_full, 1)
        export_layout.setStretchFactor(self.btn_export_clean, 1)
        right_layout.addLayout(export_layout)

        lbl_lookup = QLabel("LOOKUP TABLE")
        lbl_lookup.setWordWrap(True)
        right_layout.addWidget(lbl_lookup)
        
        self.btn_lookup_manager = QPushButton("📚 Manage Tables")
        self.btn_lookup_manager.setObjectName("actionSecondary")
        self.btn_lookup_manager.setMinimumHeight(34)
        self.btn_lookup_manager.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_lookup_manager.clicked.connect(self._open_lookup_manager)
        right_layout.addWidget(self.btn_lookup_manager)

        right_layout.addStretch()
        self.main_splitter.addWidget(right_pane)

        # Splitter Sizing
        self.main_splitter.setStretchFactor(0, 0) # Command Center
        self.main_splitter.setStretchFactor(1, 1) # Workspace
        self.main_splitter.setStretchFactor(2, 0) # Action Pane

        # Status Bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("LOADED: TBTP Masterlist")
        
        self.lbl_processor = QLabel("PROCESSOR: 92% IDLE")
        self.lbl_ai_core = QLabel("AI CORE: ChatGPT (GPT-4o)")
        self.status.addPermanentWidget(self.lbl_processor)
        self.status.addPermanentWidget(self.lbl_ai_core)

        # Dynamic Processor Update
        self._proc_timer = QTimer(self)
        self._proc_timer.timeout.connect(self._update_processor_status)
        self._proc_timer.start(2000) # Every 2 seconds

        self.processing_overlay = ProcessingOverlay(self)

        # Connect signals
        self.btn_clone_rule.clicked.connect(self._clone_rule)
        self.btn_delete_rule.clicked.connect(self._delete_rule)
        self.btn_export_full.clicked.connect(lambda: self._export("full"))
        self.btn_export_clean.clicked.connect(lambda: self._export("cleaned"))

    def _create_nav_icon(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("navIcon")
        return btn

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
            selected_path = current_item.data(0, 256) or (current_item.parent().data(0, 256) if current_item.parent() else None)

        self.library_list.clear()
        for entry in self._rule_service.list_entries():
            # Create top-level rule set item
            rs_item = QTreeWidgetItem(self.library_list)
            rs_item.setText(0, entry["rule_name"])
            rs_item.setIcon(0, QIcon.fromTheme("folder-open", QIcon("📁")))
            rs_item.setData(0, 256, entry["path"])
            rs_item.setExpanded(True)
            
            # Load columns and add colored prefixes directly under the rule set
            try:
                rs = self._rule_service.load_from_library(entry["path"])
                # Exact colors from screenshot: Magenta, Purple, Teal, Cyan
                colors = ["#F15BB5", "#9B5DE5", "#00F5D4", "#00D4FF"]
                for i, col in enumerate(rs.columns):
                    prefix = ascii_lowercase[i % 26].upper()
                    col_item = QTreeWidgetItem(rs_item)
                    col_item.setData(0, 256, entry["path"]) # Link to parent path
                    
                    # Styled text representation
                    col_item.setText(0, f"{prefix}  {col.field_id}")
                    col_item.setForeground(0, QColor(colors[i % len(colors)]))
            except Exception:
                pass

            if selected_path and entry["path"] == selected_path:
                self.library_list.setCurrentItem(rs_item)

    def _on_library_selected(self) -> None:
        item = self.library_list.currentItem()
        if not item:
            return
        
        path = None
        curr = item
        while curr:
            path = curr.data(0, 256)
            if path:
                break
            curr = curr.parent()
            
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
        dialog = StartRowDialog(self)
        if dialog.exec() != QDialog.Accepted:
            self._file_path = None
            self.file_drop.clear()
            return
        
        start_row = dialog.get_start_row()
        header_row = start_row - 1
        
        if self._rule_set:
            self._rule_set.header_row = header_row
        
        self.status.showMessage(f"Loading {Path(path).name}...")
        self.processing_overlay.show_processing("Loading File...")
        self._load_worker = FileLoadWorker(path, self._rule_set)
        self._load_worker.finished_ok.connect(self._on_file_loaded)
        self._load_worker.failed.connect(self._on_file_load_failed)
        self._load_worker.start()

    @Slot(object, str)
    def _on_file_loaded(self, df, path: str) -> None:
        self.processing_overlay.hide()
        self._file_path = path
        self._source_df = df
        self.status.showMessage(f"File loaded: {Path(path).name} ({len(df)} rows)")
        self.file_drop.set_file(path)
        try:
            self.results_view.show_preview(df, self._rule_set)
        except Exception as exc:
            QMessageBox.warning(self, "Preview", f"Could not preview file: {exc}")

    @Slot(str)
    def _on_file_load_failed(self, message: str) -> None:
        self.processing_overlay.hide()
        self._file_path = None
        self._source_df = None
        self.file_drop.clear()
        QMessageBox.warning(self, "Load Error", f"Could not load file:\n{message}")

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
        ans = QMessageBox.question(
            self, 
            "Delete Row", 
            f"Are you sure you want to delete row {row_idx + 1}?"
        )
        if ans == QMessageBox.StandardButton.Yes:
            try:
                self._result.drop_row(row_idx)
                self.results_view.show_result(self._result)
                self.status.showMessage(f"Deleted row {row_idx + 1}")
            except Exception as exc:
                QMessageBox.critical(self, "Delete Error", str(exc))

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
        path = None
        curr = item
        while curr:
            path = curr.data(0, 256)
            if path:
                break
            curr = curr.parent()
        if not path:
            return
        rs = self._rule_service.load_from_library(path)
        name = rs.rule_name
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
        if path:
            self.status.showMessage(f"Exported: {path}")
            QMessageBox.information(self, "Export", f"Saved to {path}")

    def _toggle_theme(self) -> None:
        self._dark_mode = not self._dark_mode
        apply_theme(QApplication.instance(), self._dark_mode)

    def _open_bug_report(self) -> None:
        dlg = BugReportDialog(self)
        dlg.exec()

    def _open_lookup_manager(self) -> None:
        dlg = LookupTableManagerDialog(self)
        dlg.exec()

    def _filter_library(self) -> None:
        """Filter the rule library based on search input, ignoring surrounding % symbols."""
        txt = self.search_library.text().lower()
        # Remove any % symbols used as wildcards
        txt = txt.replace('%', '')
        root = self.library_list.invisibleRootItem()
        for i in range(root.childCount()):
            rs_item = root.child(i)
            match_rs = False
            for j in range(rs_item.childCount()):
                child = rs_item.child(j)
                match = txt in child.text(0).lower()
                child.setHidden(not match)
                if match:
                    match_rs = True
            # Also check the rule set name itself
            rs_match = txt in rs_item.text(0).lower()
            rs_item.setHidden(not (match_rs or rs_match) and txt != "")
        if txt == "":
            for i in range(root.childCount()):
                rs_item = root.child(i)
                rs_item.setHidden(False)
                for j in range(rs_item.childCount()):
                    rs_item.child(j).setHidden(False)


    def _update_processor_status(self) -> None:
        """Update the processor usage indicator with actual values."""
        try:
            import psutil
            cpu_usage = psutil.cpu_percent(interval=None)
            idle = max(0, 100 - int(cpu_usage))
            self.lbl_processor.setText(f"PROCESSOR: {idle}% IDLE")
        except ImportError:
            import random
            usage = random.randint(88, 96)
            self.lbl_processor.setText(f"PROCESSOR: {usage}% IDLE (Sim)")


class ProcessingWorker(QThread):
    progress = Signal(int, str)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, rule_set, source) -> None:
        super().__init__()
        self.rule_set = rule_set
        self.source = source

    def run(self) -> None:
        try:
            pipeline = ProcessingPipeline(self.rule_set)
            result = pipeline.run(self.source, progress=lambda p, m: self.progress.emit(p, m))
            self.finished_ok.emit(result)
        except Exception as e:
            self.failed.emit(str(e))


class FileLoadWorker(QThread):
    finished_ok = Signal(object, str)
    failed = Signal(str)

    def __init__(self, file_path, rule_set) -> None:
        super().__init__()
        self.file_path = file_path
        self.rule_set = rule_set

    def run(self) -> None:
        try:
            from sheetguard.services.file_loader import FileLoader
            df = FileLoader.load(self.file_path, self.rule_set)
            self.finished_ok.emit(df, self.file_path)
        except Exception as e:
            self.failed.emit(str(e))


def run_app() -> None:
    import sys
    from sheetguard.utils.logging_config import setup_logging
    setup_logging()
    app = QApplication(sys.argv)
    apply_theme(app, dark=True)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
