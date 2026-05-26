"""Application themes (dark/light ready)."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


LIGHT_QSS = """
QMainWindow, QWidget {
    background-color: #f5f6f8;
    color: #1a1d21;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}
QFrame#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #e2e5ea;
}
QFrame#card {
    background-color: #ffffff;
    border: 1px solid #e2e5ea;
    border-radius: 8px;
}
QLabel#cardTitle {
    font-weight: 600;
    font-size: 12px;
    color: #5c6370;
}
QLabel#cardValue {
    font-size: 22px;
    font-weight: 700;
}
QPushButton {
    background-color: #2563eb;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton:hover { background-color: #1d4ed8; }
QPushButton:disabled { background-color: #94a3b8; }
QPushButton#secondary {
    background-color: #e2e8f0;
    color: #1e293b;
}
QPushButton#secondary:hover { background-color: #cbd5e1; }
QPushButton#danger { background-color: #dc2626; }
QLineEdit, QComboBox, QSpinBox, QTextEdit, QListWidget, QTableWidget {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px;
}
QTabWidget::pane { border: 1px solid #e2e5ea; border-radius: 6px; background: #fff; }
QTabBar::tab {
    background: #e2e8f0;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected { background: #ffffff; font-weight: 600; }
QProgressBar {
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    background: #e2e8f0;
    color: #1a1d21;
    text-align: center;
    min-height: 24px;
}
QProgressBar::chunk {
    background: #2563eb;
    border-radius: 8px;
}
QStatusBar { background: #ffffff; border-top: 1px solid #e2e5ea; }
"""


DARK_QSS = """
QMainWindow, QWidget {
    background-color: #0f1117;
    color: #e8eaed;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}
QFrame#sidebar {
    background-color: #161b22;
    border-right: 1px solid #30363d;
}
QFrame#card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
}
QLabel#cardTitle { font-weight: 600; font-size: 12px; color: #8b949e; }
QLabel#cardValue { font-size: 22px; font-weight: 700; color: #f0f6fc; }
QPushButton {
    background-color: #388bfd;
    color: #0d1117;
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton:hover { background-color: #58a6ff; }
QPushButton#secondary { background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; }
QLineEdit, QComboBox, QSpinBox, QTextEdit, QListWidget, QTableWidget {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px;
    color: #c9d1d9;
}
QTabWidget::pane { border: 1px solid #30363d; background: #161b22; }
QTabBar::tab { background: #21262d; padding: 8px 16px; }
QTabBar::tab:selected { background: #161b22; }
QProgressBar {
    border: 1px solid #30363d;
    border-radius: 8px;
    background: #21262d;
    color: #e8eaed;
    text-align: center;
    min-height: 24px;
}
QProgressBar::chunk {
    background: #388bfd;
    border-radius: 8px;
}
QStatusBar { background: #161b22; border-top: 1px solid #30363d; }
"""


def apply_theme(app: QApplication, dark: bool = False) -> None:
    """Apply light or dark theme to the application."""
    app.setStyleSheet(DARK_QSS if dark else LIGHT_QSS)
    if dark:
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#0f1117"))
        palette.setColor(QPalette.WindowText, QColor("#e8eaed"))
        palette.setColor(QPalette.Base, QColor("#0d1117"))
        palette.setColor(QPalette.Text, QColor("#c9d1d9"))
        palette.setColor(QPalette.Button, QColor("#21262d"))
        palette.setColor(QPalette.Highlight, QColor("#388bfd"))
        app.setPalette(palette)
