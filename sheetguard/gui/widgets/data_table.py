"""Searchable pandas-backed table widget with skeletal loading and error markers."""

from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt, Signal, QRect, QPoint
from PySide6.QtGui import QColor, QPalette, QPainter, QBrush, QPen, QPolygon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)

from sheetguard.utils.column_utils import coerce_cell


class DataTableDelegate(QStyledItemDelegate):
    """Custom delegate to render skeletal placeholders and error markers."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        # Standard background/selection
        self.initStyleOption(option, index)
        painter.save()
        
        # Check if cell is "loading" (skeletal)
        text = index.data(Qt.ItemDataRole.DisplayRole)
        is_skeletal = index.data(Qt.ItemDataRole.UserRole + 1) == "skeletal"
        has_error = index.data(Qt.ItemDataRole.UserRole + 2) == True

        # Background
        painter.fillRect(option.rect, option.palette.base())
        if option.state & QStyledItemDelegate.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        if is_skeletal:
            # Draw skeletal line
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            pen = QPen(QColor("#2D3748"), 4)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            
            w = option.rect.width() * 0.6
            h = option.rect.height()
            center_y = option.rect.top() + h / 2
            start_x = option.rect.left() + (option.rect.width() - w) / 2
            painter.drawLine(start_x, center_y, start_x + w, center_y)
        else:
            # Draw normal text
            super().paint(painter, option, index)

        # Draw Error Marker (Red Triangle in top right)
        if has_error:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QBrush(QColor("#FF4D4D")))
            painter.setPen(Qt.PenStyle.NoPen)
            
            rect = option.rect
            # Small triangle in corner
            size = 8
            poly = QPolygon([
                QPoint(rect.right() - size, rect.top()),
                QPoint(rect.right(), rect.top()),
                QPoint(rect.right(), rect.top() + size)
            ])
            painter.drawPolygon(poly)

        painter.restore()


class FrozenTable(QTableWidget):
    """A QTableWidget with a frozen first column overlay."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._frozen_table = QTableWidget(self)
        self._frozen_table.verticalHeader().hide()
        self._frozen_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._frozen_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._frozen_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._frozen_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self._frozen_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._frozen_table.setAlternatingRowColors(True)
        
        self.viewport().stackUnder(self._frozen_table)
        self.verticalScrollBar().valueChanged.connect(self._frozen_table.verticalScrollBar().setValue)
        self._frozen_table.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)
        self.horizontalHeader().sectionResized.connect(self.update_frozen_geometry)
        
        self._frozen_enabled = False
        self._frozen_table.hide()

    def set_frozen_enabled(self, enabled: bool):
        self._frozen_enabled = enabled
        self._frozen_table.setVisible(enabled)
        if enabled: self.update_frozen_geometry()

    def update_frozen_geometry(self):
        if not self._frozen_enabled: return
        hh_h = self.horizontalHeader().height()
        v_h = self.viewport().height()
        w = self.columnWidth(0) if self.columnCount() > 0 else 0
        v_header_w = self.verticalHeader().width() if not self.verticalHeader().isHidden() else 0
        self._frozen_table.setGeometry(v_header_w, 0, w, v_h + hh_h)
        self._frozen_table.setColumnWidth(0, w)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_frozen_geometry()

    def scrollTo(self, index, hint):
        if index.column() > 0: super().scrollTo(index, hint)


class DataTableWidget(QWidget):
    """High-fidelity data grid with skeletal loading and error markers."""
    cell_changed = Signal(int, str, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._table = FrozenTable()
        self._table.setSortingEnabled(True)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.EditKeyPressed)
        self._table.setMouseTracking(True)
        self._table.setShowGrid(True)
        self._table.setStyleSheet("QTableWidget { gridline-color: #1E242E; border: none; }")
        
        # Apply Delegate
        self._delegate = DataTableDelegate(self)
        self._table.setItemDelegate(self._delegate)
        self._table._frozen_table.setItemDelegate(self._delegate)
        
        self._table.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self._table)

        self._df: pd.DataFrame | None = None
        self._error_map: dict[tuple[int, str], bool] = {} # (row_idx, col_name) -> has_error
        self._editable_columns: set[str] = set()
        self._manual_edits: set[tuple[int, str]] = set()

    def set_editable_columns(self, columns: list[str]) -> None:
        self._editable_columns = set(columns)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems if columns else QTableWidget.SelectionBehavior.SelectRows)

    def set_sorting_enabled(self, enabled: bool) -> None:
        self._table.setSortingEnabled(enabled)

    def set_dataframe(self, df: pd.DataFrame | None, errors: list | None = None, action_column: str | None = None, on_action: callable | None = None) -> None:
        self._df = df.copy() if df is not None else None
        self._action_col_name = action_column
        self._action_callback = on_action
        self._error_map.clear()
        if errors:
            for e in errors:
                self._error_map[(e.row_index, e.column)] = True
        self._render(df)

    def _render(self, df: pd.DataFrame | None) -> None:
        self._table.blockSignals(True)
        self._table.clear()
        if df is None or df.empty:
            self._table.setRowCount(0)
            self._table.setColumnCount(0)
            return

        cols = list(df.columns)
        if self._action_col_name:
            cols.append(self._action_col_name)

        self._table.setRowCount(len(df))
        self._table.setColumnCount(len(cols))
        self._table.setHorizontalHeaderLabels([str(c) for c in cols])

        for r in range(len(df)):
            for c, col in enumerate(df.columns):
                val = coerce_cell(df.iloc[r, c])
                item = QTableWidgetItem()
                
                # Metadata for delegate
                original_df_idx = df.index[r]
                item.setData(Qt.ItemDataRole.UserRole, original_df_idx)
                
                if pd.isna(val) or str(val).strip() == "":
                    item.setData(Qt.ItemDataRole.UserRole + 1, "skeletal")
                else:
                    item.setText(str(val))
                
                if self._error_map.get((original_df_idx, col)):
                    item.setData(Qt.ItemDataRole.UserRole + 2, True)

                # Editing
                if col in self._editable_columns:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                # Manual edits styling
                if (original_df_idx, col) in self._manual_edits:
                    item.setForeground(QColor("#10B981"))
                
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(r, c, item)

            # Add Action Button if needed
            if self._action_col_name:
                btn_text = self._action_col_name
                if self._action_col_name == "Delete":
                    btn_text = "🗑️ Delete"
                btn = QPushButton(btn_text)
                if "Delete" in self._action_col_name:
                    btn.setObjectName("danger")
                
                # Capture row data for callback
                row_data = df.iloc[r].to_dict()
                btn.clicked.connect(lambda checked=False, d=row_data: self._action_callback(d))
                self._table.setCellWidget(r, len(cols) - 1, btn)

        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.blockSignals(False)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self._df is None: return
        col_idx = item.column()
        header = self._table.horizontalHeaderItem(col_idx)
        if not header: return
        column_name = header.text()
        
        if column_name in self._editable_columns:
            original_idx = item.data(Qt.ItemDataRole.UserRole)
            new_value = item.text()
            self._manual_edits.add((original_idx, column_name))
            item.setForeground(QColor("#10B981"))
            self.cell_changed.emit(original_idx, column_name, new_value)
