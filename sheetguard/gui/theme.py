"""Application themes (dark/light ready)."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


LIGHT_QSS = """
QMainWindow, QWidget {
    background-color: #F8FAFC;
    color: #0F172A;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}
QFrame#sidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #CBD5E1;
}
QFrame#card {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
}
QLabel#cardTitle {
    font-weight: 600;
    font-size: 12px;
    color: #475569;
}
QLabel#cardValue {
    font-size: 22px;
    font-weight: 700;
}
QPushButton {
    background-color: #2563EB;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton:hover { background-color: #1D4ED8; }
QPushButton:disabled { background-color: #94A3B8; }
QPushButton#secondary {
    background-color: #F1F5F9;
    color: #0F172A;
}
QPushButton#secondary:hover { background-color: #E2E8F0; }
QPushButton#danger { background-color: #DC2626; }
QLineEdit, QComboBox, QSpinBox, QTextEdit, QListWidget, QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 6px;
}
QTableWidget::item:hover {
    background-color: rgba(37, 99, 235, 30);
}
QTableWidget::item:selected {
    background-color: #F1F5F9;
    color: #0F172A;
}
QTabWidget::pane { border: 1px solid #CBD5E1; border-radius: 6px; background: #FFFFFF; }
QTabBar::tab {
    background: #F1F5F9;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected { background: #FFFFFF; font-weight: 600; }
QProgressBar {
    border: none;
    border-radius: 4px;
    background: #F1F5F9;
    text-align: center;
}
QProgressBar::chunk { background: #2563EB; border-radius: 4px; }
QStatusBar { background: #FFFFFF; border-top: 1px solid #CBD5E1; }
"""


DARK_QSS = """
QMainWindow, QWidget {
    background-color: #0F172A;
    color: #F8FAFC;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}
QFrame#sidebar {
    background-color: #1E293B;
    border-right: 1px solid #334155;
}
QFrame#card {
    background-color: #334155;
    border: 1px solid #475569;
    border-radius: 8px;
}
QLabel#cardTitle { font-weight: 600; font-size: 12px; color: #CBD5E1; }
QLabel#cardValue { font-size: 22px; font-weight: 700; color: #F8FAFC; }
QPushButton {
    background-color: #3B82F6;
    color: #F8FAFC;
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton:hover { background-color: #60A5FA; }
QPushButton#secondary { background-color: #1E293B; color: #CBD5E1; border: 1px solid #334155; }
QPushButton#danger { background-color: #EF4444; }
QLineEdit, QComboBox, QSpinBox, QTextEdit, QListWidget, QTableWidget {
    background-color: #0F172A;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px;
    color: #F8FAFC;
}
QTableWidget::item:hover {
    background-color: rgba(59, 130, 246, 30);
}
QTableWidget::item:selected {
    background-color: #1E293B;
    color: #F8FAFC;
}
QTabWidget::pane { border: 1px solid #334155; background: #1E293B; }
QTabBar::tab { background: #1E293B; padding: 8px 16px; color: #CBD5E1; }
QTabBar::tab:selected { background: #334155; color: #F8FAFC; }
QProgressBar { background: #1E293B; border: none; border-radius: 4px; }
QProgressBar::chunk { background: #3B82F6; }
QStatusBar { background: #1E293B; border-top: 1px solid #334155; }
"""


def apply_theme(app: QApplication, dark: bool = False) -> None:
    """Apply light or dark theme to the application."""
    app.setStyleSheet(DARK_QSS if dark else LIGHT_QSS)
    if dark:
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#0F172A"))
        palette.setColor(QPalette.WindowText, QColor("#F8FAFC"))
        palette.setColor(QPalette.Base, QColor("#0F172A"))
        palette.setColor(QPalette.Text, QColor("#F8FAFC"))
        palette.setColor(QPalette.Button, QColor("#1E293B"))
        palette.setColor(QPalette.Highlight, QColor("#3B82F6"))
        app.setPalette(palette)
    else:
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#F8FAFC"))
        palette.setColor(QPalette.WindowText, QColor("#0F172A"))
        palette.setColor(QPalette.Base, QColor("#FFFFFF"))
        palette.setColor(QPalette.Text, QColor("#0F172A"))
        palette.setColor(QPalette.Button, QColor("#F1F5F9"))
        palette.setColor(QPalette.Highlight, QColor("#2563EB"))
        app.setPalette(palette)
