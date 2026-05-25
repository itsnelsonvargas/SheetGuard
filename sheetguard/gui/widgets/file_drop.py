"""Drag-and-drop file upload widget."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class FileDropZone(QFrame):
    """Accept .xlsx and .csv files via drag-and-drop or click."""

    file_selected = Signal(str)

    ACCEPTED = {".xlsx", ".xls", ".csv"}

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setAcceptDrops(True)
        self.setMinimumHeight(100)

        layout = QVBoxLayout(self)
        self._label = QLabel("Drop Excel or CSV file here\n(.xlsx, .csv)")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if Path(url.toLocalFile()).suffix.lower() in self.ACCEPTED:
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if Path(path).suffix.lower() in self.ACCEPTED:
                self.set_file(path)
                self.file_selected.emit(path)
                break

    def set_file(self, path: str) -> None:
        name = Path(path).name
        self._label.setText(f"Loaded: {name}")

    def clear(self) -> None:
        self._label.setText("Drop Excel or CSV file here\n(.xlsx, .csv)")
