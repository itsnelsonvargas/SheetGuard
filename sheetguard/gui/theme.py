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
QFrame#sidebar QLabel {
    background-color: transparent;
}
QFrame#summaryContainer {
    background-color: transparent;
    border: none;
}
QFrame#card {
    background-color: #FFFFFF;
    border: 1px solid #0F172A;
    border-radius: 10px;
}
QFrame#card QLabel {
    background-color: transparent;
}
QLabel#cardTitle {
    background-color: transparent;
    font-weight: 600;
    font-size: 12px;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
QLabel#errorsValue, QLabel#warningsValue, QLabel#duplicatesValue, QLabel#correctionsValue {
    background-color: transparent;
    font-size: 24px;
    font-weight: 700;
}
QLabel#errorsValue { color: #DC2626; }
QLabel#warningsValue { color: #D97706; }
QLabel#duplicatesValue { color: #2563EB; }
QLabel#correctionsValue { color: #059669; }

QPushButton {
    background-color: transparent;
    color: #2563EB;
    border: 1px solid #2563EB;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 700;
}
QPushButton:hover { background-color: rgba(37, 99, 235, 20); }
QPushButton:pressed { background-color: rgba(37, 99, 235, 40); }
QPushButton:disabled { border-color: #94A3B8; color: #94A3B8; background-color: transparent; }

QPushButton#secondary {
    color: #64748B;
    border: 1px solid #64748B;
}
QPushButton#secondary:hover { background-color: rgba(100, 116, 139, 20); }
QPushButton#secondary:pressed { background-color: rgba(100, 116, 139, 40); }

QPushButton#success {
    color: #059669;
    border: 1px solid #059669;
}
QPushButton#success:hover { background-color: rgba(5, 150, 105, 20); }
QPushButton#success:pressed { background-color: rgba(5, 150, 105, 40); }

QPushButton#danger { 
    color: #DC2626; 
    border: 1px solid #DC2626;
}
QPushButton#danger:hover { background-color: rgba(220, 38, 38, 20); }
QPushButton#danger:pressed { background-color: rgba(220, 38, 38, 40); }

QLineEdit, QComboBox, QTextEdit, QListWidget, QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 8px;
}
QListWidget#ruleLibrary {
    padding: 4px;
    outline: none;
}
QListWidget#ruleLibrary::item {
    border-radius: 5px;
    padding: 8px 10px;
    margin: 1px 0;
}
QListWidget#ruleLibrary::item:hover {
    background-color: rgba(37, 99, 235, 20);
}
QListWidget#ruleLibrary::item:selected {
    background-color: #DBEAFE;
    color: #0F172A;
    font-weight: 700;
}
QListWidget#ruleLibrary::item:selected:!active {
    background-color: #DBEAFE;
    color: #0F172A;
}
QSpinBox {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 6px;
    padding-right: 20px; /* Make room for buttons */
}
QSpinBox::up-button, QSpinBox::down-button {
    width: 20px;
    border: none;
    background-color: #F1F5F9;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #E2E8F0;
}
QSpinBox::up-arrow { image: url(none); border-left: 4px solid transparent; border-right: 4px solid transparent; border-bottom: 5px solid #64748B; width: 0; height: 0; }
QSpinBox::down-arrow { image: url(none); border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #64748B; width: 0; height: 0; }

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
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    background: #F1F5F9;
    color: #0F172A;
    text-align: center;
    min-height: 24px;
}
QProgressBar::chunk {
    background: #2563EB;
    border-radius: 8px;
}
QStatusBar { background: #FFFFFF; border-top: 1px solid #CBD5E1; }
QLabel#bugReportHeader {
    font-size: 18px;
    font-weight: 700;
    color: #0F172A;
}
QLabel#bugReportSubtitle {
    font-size: 12px;
    color: #64748B;
    margin-bottom: 4px;
}
QLabel#bugReportInfoLabel {
    font-size: 11px;
    color: #64748B;
    margin-top: 8px;
}
QLabel#bugReportInfoPreview {
    font-size: 11px;
    color: #94A3B8;
    background-color: #F1F5F9;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 8px;
}
QPushButton#bug_link {
    background-color: transparent;
    color: #64748B;
    border: 1px dashed #94A3B8;
    font-weight: 600;
    font-size: 12px;
}
QPushButton#bug_link:hover {
    color: #0F172A;
    border-color: #64748B;
    background-color: rgba(100, 116, 139, 15);
}
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
QFrame#sidebar QLabel {
    background-color: transparent;
}
QFrame#summaryContainer {
    background-color: transparent;
    border: none;
}
QFrame#card {
    background-color: #1E293B;
    border: 1px solid #0F172A;
    border-radius: 10px;
}
QFrame#card QLabel {
    background-color: transparent;
}
QLabel#cardTitle {
    background-color: transparent;
    font-weight: 600;
    font-size: 12px;
    color: #CBD5E1;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
QLabel#errorsValue, QLabel#warningsValue, QLabel#duplicatesValue, QLabel#correctionsValue {
    background-color: transparent;
    font-size: 24px;
    font-weight: 700;
}
QLabel#errorsValue { color: #EF4444; }
QLabel#warningsValue { color: #F59E0B; }
QLabel#duplicatesValue { color: #06B6D4; }
QLabel#correctionsValue { color: #10B981; }

QPushButton {
    background-color: #3B82F6;
    color: #F8FAFC;
    border: 1px solid #2563EB;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 700;
}
QPushButton:hover { background-color: #60A5FA; }
QPushButton:pressed { background-color: #2563EB; }
QPushButton:disabled { background-color: #334155; color: #475569; }

QPushButton#success {
    background-color: #10B981;
    border: 1px solid #059669;
    color: #0F172A;
}
QPushButton#success:hover { background-color: #34D399; }
QPushButton#success:pressed { background-color: #059669; }

QPushButton#danger { 
    background-color: #EF4444; 
    border: 1px solid #DC2626;
    color: #F8FAFC;
}
QPushButton#danger:hover { background-color: #F87171; }
QPushButton#danger:pressed { background-color: #DC2626; }

QLineEdit, QComboBox, QTextEdit, QListWidget, QTableWidget {
    background-color: #0F172A;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px;
    color: #F8FAFC;
}
QListWidget#ruleLibrary {
    padding: 4px;
    outline: none;
}
QListWidget#ruleLibrary::item {
    border-radius: 5px;
    padding: 8px 10px;
    margin: 1px 0;
}
QListWidget#ruleLibrary::item:hover {
    background-color: rgba(59, 130, 246, 45);
}
QListWidget#ruleLibrary::item:selected {
    background-color: #2563EB;
    color: #F8FAFC;
    font-weight: 700;
}
QListWidget#ruleLibrary::item:selected:!active {
    background-color: #2563EB;
    color: #F8FAFC;
}
QSpinBox {
    background-color: #0F172A;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px;
    padding-right: 20px;
    color: #F8FAFC;
}
QSpinBox::up-button, QSpinBox::down-button {
    width: 20px;
    border: none;
    background-color: #1E293B;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #334155;
}
QSpinBox::up-arrow { image: url(none); border-left: 4px solid transparent; border-right: 4px solid transparent; border-bottom: 5px solid #CBD5E1; width: 0; height: 0; }
QSpinBox::down-arrow { image: url(none); border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #CBD5E1; width: 0; height: 0; }

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
QProgressBar {
    border: 1px solid #334155;
    border-radius: 8px;
    background: #1E293B;
    color: #F8FAFC;
    text-align: center;
    min-height: 24px;
}
QProgressBar::chunk {
    background: #3B82F6;
    border-radius: 8px;
}
QStatusBar { background: #1E293B; border-top: 1px solid #334155; }
QLabel#bugReportHeader {
    font-size: 18px;
    font-weight: 700;
    color: #F8FAFC;
}
QLabel#bugReportSubtitle {
    font-size: 12px;
    color: #94A3B8;
    margin-bottom: 4px;
}
QLabel#bugReportInfoLabel {
    font-size: 11px;
    color: #94A3B8;
    margin-top: 8px;
}
QLabel#bugReportInfoPreview {
    font-size: 11px;
    color: #64748B;
    background-color: #0F172A;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px;
}
QPushButton#bug_link {
    background-color: transparent;
    color: #94A3B8;
    border: 1px dashed #475569;
    font-weight: 600;
    font-size: 12px;
}
QPushButton#bug_link:hover {
    color: #F8FAFC;
    border-color: #94A3B8;
    background-color: rgba(148, 163, 184, 15);
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
