"""Processing overlay to show during long-running tasks."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget,
    QProgressBar,
)


class ProcessingOverlay(QFrame):
    """Semi-transparent overlay with a spinner and progress information."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("processingOverlay")
        self.setFrameShape(QFrame.NoFrame)
        
        # Style the overlay to be semi-transparent and centered
        self.setStyleSheet("""
            QFrame#processingOverlay {
                background-color: rgba(15, 23, 42, 180);
                border-radius: 0px;
            }
            QFrame#contentContainer {
                background-color: #1E293B;
                border: 2px solid #3B82F6;
                border-radius: 12px;
                min-width: 300px;
                max-width: 400px;
                padding: 30px;
            }
            QLabel#processingTitle {
                background-color: transparent;
                color: #F8FAFC;
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 10px;
            }
            QLabel#processingMsg {
                background-color: transparent;
                color: #CBD5E1;
                font-size: 14px;
                margin-bottom: 20px;
            }
            QProgressBar {
                border: 1px solid #334155;
                border-radius: 6px;
                background: #0F172A;
                color: #F8FAFC;
                text-align: center;
                height: 12px;
            }
            QProgressBar::chunk {
                background: #3B82F6;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        container = QFrame()
        container.setObjectName("contentContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(10)
        container_layout.setAlignment(Qt.AlignCenter)

        self.title_label = QLabel("Processing Data")
        self.title_label.setObjectName("processingTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.title_label)

        self.msg_label = QLabel("Please wait while we clean and validate...")
        self.msg_label.setObjectName("processingMsg")
        self.msg_label.setAlignment(Qt.AlignCenter)
        self.msg_label.setWordWrap(True)
        container_layout.addWidget(self.msg_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        container_layout.addWidget(self.progress_bar)

        layout.addWidget(container)
        self.hide()

    def update_progress(self, pct: int, msg: str) -> None:
        """Update the overlay with current progress."""
        self.progress_bar.setValue(pct)
        self.msg_label.setText(msg)

    def show_processing(self, title: str = "Processing Data") -> None:
        """Show the overlay and reset progress."""
        self.title_label.setText(title)
        self.progress_bar.setValue(0)
        self.show()
        self.raise_()

    def resizeEvent(self, event) -> None:
        """Ensure the overlay covers the entire parent."""
        if self.parentWidget():
            self.setGeometry(self.parentWidget().rect())
        super().resizeEvent(event)
