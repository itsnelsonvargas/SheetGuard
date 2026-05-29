"""Bug report dialog for SheetGuard."""

from __future__ import annotations

import platform
import sys
import webbrowser
from urllib.parse import quote

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class BugReportDialog(QDialog):
    """Dialog for composing and sending a bug report via email."""

    RECIPIENT = "itsnelsonvargas@gmail.com"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Submit a Bug Report")
        self.setMinimumSize(520, 480)
        self.setObjectName("bugReportDialog")
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        # Header
        header = QLabel("Submit a Bug Report")
        header.setObjectName("bugReportHeader")
        layout.addWidget(header)

        subtitle = QLabel(
            "Describe the issue you encountered. You can either open Gmail in your "
            "browser, or copy the report to your clipboard to paste into any email app."
        )
        subtitle.setObjectName("bugReportSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Form
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.input_title = QLineEdit()
        self.input_title.setPlaceholderText("e.g. App crashes when exporting report")
        form.addRow("Title:", self.input_title)

        self.input_description = QTextEdit()
        self.input_description.setPlaceholderText(
            "What happened? Provide as much detail as possible."
        )
        self.input_description.setMinimumHeight(80)
        form.addRow("Description:", self.input_description)

        self.input_steps = QTextEdit()
        self.input_steps.setPlaceholderText(
            "1. Open the app\n2. Click on …\n3. See error"
        )
        self.input_steps.setMinimumHeight(80)
        form.addRow("Steps to\nReproduce:", self.input_steps)

        self.input_expected = QLineEdit()
        self.input_expected.setPlaceholderText(
            "What did you expect to happen instead?"
        )
        form.addRow("Expected\nBehavior:", self.input_expected)

        layout.addLayout(form)

        # System info preview
        self._sys_info = self._collect_system_info()
        info_label = QLabel("System info will be attached automatically:")
        info_label.setObjectName("bugReportInfoLabel")
        layout.addWidget(info_label)

        info_preview = QLabel(self._sys_info)
        info_preview.setObjectName("bugReportInfoPreview")
        info_preview.setWordWrap(True)
        info_preview.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(info_preview)

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("✖ Cancel")
        btn_cancel.setObjectName("secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_copy = QPushButton("📋 Copy to Clipboard")
        btn_copy.setObjectName("secondary")
        btn_copy.clicked.connect(self._copy_to_clipboard)
        btn_row.addWidget(btn_copy)

        btn_gmail = QPushButton("📧 Open in Gmail")
        btn_gmail.setObjectName("success")
        btn_gmail.clicked.connect(self._open_in_gmail)
        btn_row.addWidget(btn_gmail)

        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _collect_system_info() -> str:
        """Return a short system-info string."""
        lines = [
            f"OS: {platform.system()} {platform.release()} ({platform.version()})",
            f"Python: {sys.version.split()[0]}",
            f"Architecture: {platform.machine()}",
        ]
        try:
            import PySide6
            lines.append(f"PySide6: {PySide6.__version__}")
        except Exception:
            pass
        return "\n".join(lines)

    def _get_report_data(self) -> tuple[str, str, str] | None:
        """Validate inputs and return (title, subject, body). Returns None if invalid."""
        title = self.input_title.text().strip()
        description = self.input_description.toPlainText().strip()

        if not title:
            QMessageBox.warning(self, "Missing Title", "Please enter a bug title.")
            self.input_title.setFocus()
            return None
        if not description:
            QMessageBox.warning(
                self, "Missing Description", "Please describe the issue."
            )
            self.input_description.setFocus()
            return None

        steps = self.input_steps.toPlainText().strip()
        expected = self.input_expected.text().strip()

        body_parts = [
            "--- Bug Report ---",
            "",
            f"Title: {title}",
            "",
            "Description:",
            description,
        ]
        if steps:
            body_parts += ["", "Steps to Reproduce:", steps]
        if expected:
            body_parts += ["", "Expected Behavior:", expected]
        body_parts += [
            "",
            "--- System Info ---",
            self._sys_info,
        ]
        body = "\n".join(body_parts)
        subject = f"[SheetGuard Bug] {title}"

        return title, subject, body

    def _copy_to_clipboard(self) -> None:
        """Copy the formatted bug report to the clipboard."""
        data = self._get_report_data()
        if not data:
            return
        _, subject, body = data

        clipboard = QApplication.clipboard()
        clipboard_text = f"To: {self.RECIPIENT}\nSubject: {subject}\n\n{body}"
        clipboard.setText(clipboard_text)

        QMessageBox.information(
            self,
            "Copied",
            f"The bug report has been copied to your clipboard.\n\n"
            f"Please paste it into your email app and send it to:\n{self.RECIPIENT}",
        )
        self.accept()

    def _open_in_gmail(self) -> None:
        """Open the default browser directly to the Gmail compose window."""
        data = self._get_report_data()
        if not data:
            return
        _, subject, body = data

        gmail_url = (
            f"https://mail.google.com/mail/?view=cm&fs=1"
            f"&to={self.RECIPIENT}"
            f"&su={quote(subject, safe='')}"
            f"&body={quote(body, safe='')}"
        )

        try:
            webbrowser.open(gmail_url)
        except Exception:
            pass

        # Also copy as a backup
        clipboard = QApplication.clipboard()
        clipboard_text = f"To: {self.RECIPIENT}\nSubject: {subject}\n\n{body}"
        clipboard.setText(clipboard_text)

        QMessageBox.information(
            self,
            "Gmail Opened",
            "We opened Gmail in your browser.\n\n"
            "(We also copied the report to your clipboard just in case!)",
        )
        self.accept()
