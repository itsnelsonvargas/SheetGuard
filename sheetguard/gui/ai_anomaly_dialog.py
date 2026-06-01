"""Dialog to display AI Anomaly Scan results."""

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QLabel,
)

class AIAnomalyDialog(QDialog):
    """Dialog to render markdown anomaly scan results from the AI."""
    
    def __init__(self, report_markdown: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI Anomaly Report")
        self.setMinimumSize(800, 600)
        self.setObjectName("aiAnomalyDialog")
        
        self.report_markdown = report_markdown
        self._build_ui()
    
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        header = QLabel("🔍 AI Anomaly Detection Results")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #E11D48;")
        layout.addWidget(header)
        
        description = QLabel(
            "This report highlights suspicious data points, logical inconsistencies, "
            "and potential outliers found in your dataset sample."
        )
        description.setStyleSheet("color: #64748B; font-size: 12px;")
        description.setWordWrap(True)
        layout.addWidget(description)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMarkdown(self.report_markdown)
        self.text_edit.setObjectName("aiAnomalyText")
        self.text_edit.setStyleSheet("font-size: 14px; padding: 10px; background-color: #FFF1F2; color: #881337;")
        layout.addWidget(self.text_edit)
        
        btn_row = QHBoxLayout()
        
        btn_export = QPushButton("📄 Export Report...")
        btn_export.setObjectName("secondary")
        btn_export.clicked.connect(self._export_report)
        btn_row.addWidget(btn_export)
        
        btn_row.addStretch()
        
        btn_close = QPushButton("✖ Close")
        btn_close.setObjectName("success")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        
        layout.addLayout(btn_row)

    def _export_report(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Anomaly Report", "anomaly_report.md", "Markdown Files (*.md);;Text Files (*.txt)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.report_markdown)
                QMessageBox.information(self, "Export Successful", f"Report saved to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Could not save file:\n{e}")
