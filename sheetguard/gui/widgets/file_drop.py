"""Drag-and-drop file upload widget."""

from __future__ import annotations

import os
import platform
import subprocess
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
        self._label.setOpenExternalLinks(False)
        self._label.linkActivated.connect(self._on_link_clicked)
        layout.addWidget(self._label)
        self._current_path: str | None = None

    def _on_link_clicked(self, link: str) -> None:
        if link == "open_folder" and self._current_path:
            path = Path(self._current_path).parent
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])

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
        self._current_path = path
        name = Path(path).name
        # Use HTML link for clickability
        self._label.setText(
            f'Loaded: <a href="open_folder" style="color: #2563eb; text-decoration: none; font-weight: bold;">{name}</a>'
            '<br><small style="color: #64748b;">(click to open folder)</small>'
        )

    def clear(self) -> None:
        self._current_path = None
        self._label.setText("Drop Excel or CSV file here\n(.xlsx, .csv)")
