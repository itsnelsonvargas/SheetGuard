"""Dialog to display AI Insights."""

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

class AIInsightsDialog(QDialog):
    """Dialog to render markdown insights from the AI."""
    
    def __init__(self, insights_markdown: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI Data Insights")
        self.setMinimumSize(700, 500)
        self.setObjectName("aiInsightsDialog")
        
        self.insights_markdown = insights_markdown
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        # QTextEdit has limited markdown support, but sufficient for basic bold/lists
        text_edit.setMarkdown(self.insights_markdown)
        text_edit.setObjectName("aiInsightsText")
        # Ensure it has a white/dark background based on theme instead of transparent
        text_edit.setStyleSheet("font-size: 14px; padding: 10px;")
        layout.addWidget(text_edit)
        
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        btn_close = QPushButton("Close")
        btn_close.setObjectName("success")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        
        layout.addLayout(btn_row)
