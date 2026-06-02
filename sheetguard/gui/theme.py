"""Application themes (dark/light ready)."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


LIGHT_QSS = """
QMainWindow, QWidget {
    background-color: #F8FAFC;
    color: #0F172A;
    font-family: "Inter", "Segoe UI", sans-serif;
    font-size: 13px;
}
QFrame#sidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #CBD5E1;
}
QFrame#sidebar QLabel {
    background-color: transparent;
    font-weight: 700;
    font-size: 11px;
    color: #64748B;
    margin-top: 10px;
}
QFrame#summaryContainer {
    background-color: transparent;
    border: none;
}
QFrame#card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
}
QFrame#card QLabel {
    background-color: transparent;
}
QLabel#cardTitle {
    background-color: transparent;
    font-weight: 600;
    font-size: 11px;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
QLabel#errorsValue, QLabel#warningsValue, QLabel#duplicatesValue, QLabel#correctionsValue {
    background-color: transparent;
    font-size: 28px;
    font-weight: 800;
}
QLabel#errorsValue { color: #EF4444; }
QLabel#warningsValue { color: #F59E0B; }
QLabel#duplicatesValue { color: #0EA5E9; }
QLabel#correctionsValue { color: #10B981; }

QPushButton {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton:hover { background-color: #F1F5F9; border-color: #94A3B8; }
QPushButton:pressed { background-color: #E2E8F0; }
QPushButton:disabled { color: #94A3B8; background-color: #F8FAFC; }

QPushButton#primary {
    background-color: #0F172A;
    color: #FFFFFF;
    border: none;
}
QPushButton#primary:hover { background-color: #1E293B; }

QPushButton#secondary {
    background-color: transparent;
    color: #64748B;
    border: 1px solid #CBD5E1;
}

QLineEdit, QComboBox, QTextEdit, QListWidget, QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 8px;
}
QTabWidget::pane { border: 1px solid #E2E8F0; border-radius: 12px; background: #FFFFFF; }
QTabBar::tab {
    background: #F1F5F9;
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    color: #64748B;
    font-weight: 600;
}
QTabBar::tab:selected { background: #FFFFFF; color: #0F172A; border: 1px solid #E2E8F0; border-bottom: none; }

QProgressBar {
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    background: #F1F5F9;
    text-align: center;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0EA5E9, stop:1 #2DD4BF);
    border-radius: 10px;
}
"""

DARK_QSS = """
QMainWindow, QWidget {
    background-color: #0B0E14;
    color: #E2E8F0;
    font-family: "Inter", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* Branding Area */
QLabel#brandTitle {
    font-size: 16px;
    font-weight: 900;
    color: #FFFFFF;
    letter-spacing: 0.5px;
}
QLabel#brandIcon {
    font-size: 20px;
    color: #00D4FF;
}

/* Icon Sidebar (Far Left Navigation Strip) */
QFrame#iconSidebar {
    background-color: #0B0E14;
    border-right: 1px solid #1E242E;
    min-width: 35px;
    max-width: 35px;
}
QPushButton#navIcon {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 0px;
    margin-top: 8px;
    margin-bottom: 8px;
    margin-left: 2px;
    font-size: 18px;
    color: #FFFFFF;
    min-height: 30px;
    max-height: 30px;
    min-width: 30px;
    max-width: 30px;
    text-align: center;
}
QPushButton#navIcon:hover {
    background-color: #1E242E;
    color: #00D4FF;
}
QPushButton#navIcon[active="true"] {
    background-color: #1A1F29;
    color: #00D4FF;
    border-left: 2px solid #00D4FF;
}


/* Command Center Panel */
QFrame#sidebar {
    background-color: #151921;
    border-right: 1px solid #1E242E;
}
QLabel#groupHeader {
    background-color: transparent;
    font-weight: 800;
    font-size: 11px;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-top: 15px;
    margin-bottom: 5px;
}

/* Scroll Area for Command Center Content */
QScrollArea#sidebarScroll {
    background-color: transparent;
    border: none;
}
QFrame#sidebarContent {
    background-color: transparent;
}

/* Fixed Bottom Container in Sidebar */
QFrame#sidebarBottom {
    background-color: #151921;
    border-top: 1px solid #1E242E;
}

/* Browse Button Gradient (Blue to Cyan) */
QPushButton#browseAction {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4D79FF, stop:1 #00D4FF);
    color: #FFFFFF;
    border: none;
    font-weight: 700;
    border-radius: 6px;
    padding: 10px;
}
QPushButton#browseAction:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #668CFF, stop:1 #33E0FF);
}

/* Standard Secondary Buttons */
QPushButton#actionSecondary {
    background-color: #2D3748;
    color: #E2E8F0;
    border: none;
    border-radius: 6px;
    padding: 8px;
    font-weight: 600;
}
QPushButton#actionSecondary:hover {
    background-color: #4A5568;
}

/* Delete Button (Magenta) */
QPushButton#deleteAction {
    background-color: #F15BB5;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px;
    font-weight: 700;
}
QPushButton#deleteAction:hover {
    background-color: #F587C9;
}

/* Batch Upload Drop Zone */
QFrame#dropZone {
    background-color: #1A1F29;
    border: 1px dashed #2D3748;
    border-radius: 8px;
    margin: 5px 0px;
}
QFrame#dropZone:hover {
    border-color: #00D4FF;
    background-color: #1E242E;
}

/* Tree View Styling */
QTreeWidget#ruleLibrary {
    background-color: transparent;
    border: none;
    font-size: 13px;
    color: #E2E8F0;
    outline: none;
}
QTreeWidget#ruleLibrary::item {
    padding: 6px 0px;
}
QTreeWidget#ruleLibrary::item:selected {
    background-color: #1A1F29;
    color: #00D4FF;
    border-radius: 4px;
}

/* Dashboard Score Dial Placeholder */
QFrame#scoreDial {
    background: qconicalgradient(cx:0.5, cy:0.5, angle:90, stop:0 #F15BB5, stop:0.87 #00D4FF, stop:0.88 #242B38);
    border-radius: 35px;
    min-width: 70px;
    max-width: 70px;
    min-height: 70px;
    max-height: 70px;
}

/* General Layout Elements */
QSplitter::handle {
    background-color: #1E242E;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #1E242E;
    border-radius: 4px;
    background: #0B0E14;
}
QTabBar::tab {
    background: #151921;
    color: #94A3B8;
    padding: 10px 24px;
    margin-right: 2px;
    font-weight: 600;
}
QTabBar::tab:top {
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    border-bottom: none;
}
QTabBar::tab:bottom {
    border-bottom-left-radius: 4px;
    border-bottom-right-radius: 4px;
    border-top: 1px solid #1E242E;
    margin-top: 0px;
    background: #1A1F29;
    color: #E2E8F0;
}
QTabBar::tab:selected:bottom {
    background: #0B0E14;
    color: #00D4FF;
    border-top: 2px solid #00D4FF;
}

QStatusBar {
    background-color: #151921;
    border-top: 1px solid #1E242E;
    color: #94A3B8;
    font-size: 11px;
}
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
