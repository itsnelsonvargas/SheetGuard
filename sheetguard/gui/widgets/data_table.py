"""Searchable pandas-backed table widget."""

from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
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
)

from sheetguard.utils.column_utils import coerce_cell


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
        
        # Ensure it sits on top of the main table's viewport
        self.viewport().stackUnder(self._frozen_table)
        
        # Sync vertical scroll
        self.verticalScrollBar().valueChanged.connect(self._frozen_table.verticalScrollBar().setValue)
        self._frozen_table.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)
        
        # Sync header resize
        self.horizontalHeader().sectionResized.connect(self.update_frozen_geometry)
        
        self._frozen_enabled = False
        self._frozen_table.hide()

    def set_frozen_enabled(self, enabled: bool):
        self._frozen_enabled = enabled
        self._frozen_table.setVisible(enabled)
        if enabled:
            self.update_frozen_geometry()

    def update_frozen_geometry(self):
        if not self._frozen_enabled:
            return
        
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
        if index.column() > 0:
            super().scrollTo(index, hint)


class DataTableWidget(QWidget):
    """Table with search/filter for preview and results."""
    cell_changed = Signal(int, str, str)  # original_row_index, column_name, new_value

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        # Add padding around the entire tab content
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        bar_layout = QHBoxLayout()
        bar_layout.setSpacing(10)
        
        search_label = QLabel("Search:")
        search_label.setStyleSheet("font-weight: bold; color: #64748b;")
        bar_layout.addWidget(search_label)
        
        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter rows...")
        self._search.setMinimumHeight(36)
        self._search.textChanged.connect(self._apply_filter)
        bar_layout.addWidget(self._search)
        
        # Add vertical space top and bottom for the search bar area
        bar_container = QWidget()
        bar_container.setLayout(bar_layout)
        layout.addWidget(bar_container)

        self._table = FrozenTable()
        self._table.setSortingEnabled(True)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.EditKeyPressed)
        self._table.setMouseTracking(True)
        self._table.cellEntered.connect(self._on_cell_entered)
        self._table._frozen_table.cellEntered.connect(self._on_cell_entered)
        self._table.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self._table)

        self._df: pd.DataFrame | None = None
        self._action_col_name: str | None = None
        self._action_callback: callable | None = None
        self._hovered_row: int = -1
        self._hidden_columns: set[str] = set()
        self._freeze_first_column: bool = False
        self._sorting_enabled: bool = True
        self._editable_columns: set[str] = set()
        self._manual_edits: set[tuple[int, str]] = set()  # (original_df_index, column_name)

    def set_editable_columns(self, columns: list[str]) -> None:
        """Define which columns should be user-editable."""
        self._editable_columns = set(columns)
        if self._editable_columns:
            # When editing is allowed, we want to select specific items, not entire rows
            self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        else:
            self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

    def set_sorting_enabled(self, enabled: bool) -> None:
        """Enable or disable sorting for this table."""
        self._sorting_enabled = enabled
        self._table.setSortingEnabled(enabled)

    def set_freeze_first_column(self, freeze: bool) -> None:
        """Enable/disable freezing of the first column."""
        self._freeze_first_column = freeze
        self._table.set_frozen_enabled(freeze and not self._is_first_col_hidden())
        if self._df is not None:
            self._render(self._df)

    def hide_column(self, column_name: str) -> None:
        """Hide a column by name across renders."""
        self._hidden_columns.add(column_name)
        if self._df is not None:
            self._render(self._df)

    def show_column(self, column_name: str) -> None:
        """Show a previously hidden column by name."""
        self._hidden_columns.discard(column_name)
        if self._df is not None:
            self._render(self._df)

    def _is_first_col_hidden(self) -> bool:
        return bool(self._df is not None and len(self._df.columns) > 0 and list(self._df.columns)[0] in self._hidden_columns)

    def _get_row_background(self, row_idx: int, is_group_header: bool = False) -> QColor:
        """Get the appropriate background color for a row based on theme and state."""
        # Use palette to detect if we are in dark mode
        is_dark = self.palette().color(QPalette.Window).lightness() < 128
        
        if is_group_header:
            return QColor("#1E293B") if is_dark else QColor("#F1F5F9")

        if self._table._frozen_enabled:
            return QColor("#0F172A") if is_dark else QColor("#FFFFFF")

        # Match standard QTableWidget alternating colors
        if self._table.alternatingRowColors() and row_idx % 2:
            return QColor("#1E293B") if is_dark else QColor("#F8FAFC")
        return QColor("#0F172A") if is_dark else QColor("#FFFFFF")
    def _on_cell_entered(self, row: int, column: int) -> None:
        """Visual feedback: highlight the entire row on hover."""
        if row == self._hovered_row:
            return
        
        # Clear old hover
        if self._hovered_row != -1:
            for c in range(self._table.columnCount()):
                item = self._table.item(self._hovered_row, c)
                if item:
                    item.setData(Qt.ItemDataRole.BackgroundRole, None)
            
            if self._table._frozen_enabled:
                item = self._table._frozen_table.item(self._hovered_row, 0)
                if item:
                    # Restore the solid background instead of setting to None
                    is_header = False
                    if self._df is not None:
                        first_val = self._df.iloc[self._hovered_row, 0]
                        other_vals = self._df.iloc[self._hovered_row, 1:]
                        if pd.notna(first_val) and str(first_val).strip() and (other_vals.isna().all() or (other_vals.astype(str).str.strip() == "").all()):
                            is_header = True
                    item.setBackground(self._get_row_background(self._hovered_row, is_header))
        
        self._hovered_row = row
        
        # Subtle semi-transparent highlight (works in light/dark)
        highlight = QColor(100, 150, 255, 40) 
        for c in range(self._table.columnCount()):
            item = self._table.item(self._hovered_row, c)
            if item:
                item.setBackground(highlight)
        
        if self._table._frozen_enabled:
            item = self._table._frozen_table.item(self._hovered_row, 0)
            if item:
                item.setBackground(highlight)

    def leaveEvent(self, event) -> None:
        """Clear hover when mouse leaves the widget area."""
        if self._hovered_row != -1:
            for c in range(self._table.columnCount()):
                item = self._table.item(self._hovered_row, c)
                if item:
                    item.setData(Qt.ItemDataRole.BackgroundRole, None)
            
            if self._table._frozen_enabled:
                item = self._table._frozen_table.item(self._hovered_row, 0)
                if item:
                    is_header = False
                    if self._df is not None:
                        first_val = self._df.iloc[self._hovered_row, 0]
                        other_vals = self._df.iloc[self._hovered_row, 1:]
                        if pd.notna(first_val) and str(first_val).strip() and (other_vals.isna().all() or (other_vals.astype(str).str.strip() == "").all()):
                            is_header = True
                    item.setBackground(self._get_row_background(self._hovered_row, is_header))
                    
            self._hovered_row = -1
        super().leaveEvent(event)

    def set_dataframe(self, df: pd.DataFrame | None, action_column: str | None = None, on_action: callable | None = None) -> None:
        self._df = df.copy() if df is not None else None
        self._action_col_name = action_column
        self._action_callback = on_action
        self._manual_edits.clear()  # Clear edit history for new datasets
        self._search.clear()
        self._render(df)

    def _render(self, df: pd.DataFrame | None) -> None:
        self._table.blockSignals(True)
        self._table.setSortingEnabled(False)
        self._table.clear()
        if self._table._frozen_enabled:
            self._table._frozen_table.clear()

        if df is None or df.empty:
            self._table.setRowCount(0)
            self._table.setColumnCount(0)
            if self._table._frozen_enabled:
                self._table._frozen_table.setRowCount(0)
                self._table._frozen_table.setColumnCount(0)
            return

        # Reconcile frozen overlay state with column hiding.
        self._table.set_frozen_enabled(self._freeze_first_column and not self._is_first_col_hidden())

        cols = list(df.columns)
        if self._action_col_name:
            cols.append(self._action_col_name)

        self._table.setRowCount(len(df))
        self._table.setColumnCount(len(cols))
        self._table.setHorizontalHeaderLabels([str(c) for c in cols])

        for idx, col in enumerate(cols):
            if col in self._hidden_columns:
                self._table.setColumnHidden(idx, True)
            else:
                self._table.setColumnHidden(idx, False)
        
        if self._table._frozen_enabled:
            self._table._frozen_table.setRowCount(len(df))
            self._table._frozen_table.setColumnCount(1)
            self._table._frozen_table.setHorizontalHeaderLabels([str(cols[0])])

        for r in range(len(df)):
            # Detect group header (only 1st column has value, others are null/empty)
            is_group_header = False
            first_val = df.iloc[r, 0]
            if pd.notna(first_val) and str(first_val).strip():
                other_vals = df.iloc[r, 1:]
                if other_vals.isna().all() or (other_vals.astype(str).str.strip() == "").all():
                    is_group_header = True

            if is_group_header:
                font = self._table.font()
                font.setBold(True)
                
                if self._table._frozen_enabled:
                    # Category headers should stay in the scrolling area (cols 1+), not the frozen column
                    # Main Table: Empty col 0, text in col 1 (spanned)
                    item_c0 = QTableWidgetItem("")
                    item_c0.setBackground(self._get_row_background(r, True))
                    self._table.setItem(r, 0, item_c0)
                    
                    item_c1 = QTableWidgetItem(str(first_val))
                    item_c1.setFlags(item_c1.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item_c1.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    item_c1.setFont(font)
                    item_c1.setBackground(self._get_row_background(r, True))
                    self._table.setItem(r, 1, item_c1)
                    self._table.setSpan(r, 1, 1, self._table.columnCount() - 1)
                    
                    # Frozen Table: Empty background for the category row
                    frozen_item = QTableWidgetItem("")
                    frozen_item.setFlags(frozen_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    frozen_item.setBackground(self._get_row_background(r, True)) 
                    self._table._frozen_table.setItem(r, 0, frozen_item)
                else:
                    item = QTableWidgetItem(str(first_val))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    item.setFont(font)
                    item.setBackground(self._get_row_background(r, True))
                    self._table.setItem(r, 0, item)
                    self._table.setSpan(r, 0, 1, self._table.columnCount())
                continue

            for c, col in enumerate(df.columns):
                val = coerce_cell(df.iloc[r, c])
                item = QTableWidgetItem(str(val))
                
                # Store original index to map back during edits/filtering
                original_df_idx = df.index[r]
                item.setData(Qt.ItemDataRole.UserRole, original_df_idx)

                if col in self._editable_columns:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                # Apply highlight for manual edits
                if (original_df_idx, col) in self._manual_edits:
                    item.setForeground(QColor("#10B981"))  # Success Green
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                
                # Center align data cells
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                if c == 0 and self._table._frozen_enabled:
                    # Hide text in main table for frozen column to avoid double rendering
                    item.setForeground(QColor(0, 0, 0, 0))

                self._table.setItem(r, c, item)
                
                if c == 0 and self._table._frozen_enabled:
                    frozen_item = QTableWidgetItem(str(val))
                    frozen_item.setFlags(frozen_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    frozen_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    # Use white text for contrast on dark background
                    frozen_item.setForeground(QColor("#F8FAFC")) 
                    frozen_item.setBackground(self._get_row_background(r, False))
                    self._table._frozen_table.setItem(r, 0, frozen_item)
            
            if self._action_col_name:
                btn = QPushButton(self._action_col_name)
                if "Delete" in self._action_col_name:
                    btn.setObjectName("danger")
                
                # Capture row data for callback
                row_data = df.iloc[r].to_dict()
                btn.clicked.connect(lambda checked=False, d=row_data: self._action_callback(d))
                self._table.setCellWidget(r, len(cols) - 1, btn)

        self._table.resizeColumnsToContents()
        if self._table._frozen_enabled:
            # Sync row heights
            for r in range(self._table.rowCount()):
                self._table._frozen_table.setRowHeight(r, self._table.rowHeight(r))
            self._table.update_frozen_geometry()
            
        if self._sorting_enabled:
            self._table.setSortingEnabled(True)
        self._table.blockSignals(False)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        """Handle manual cell edits."""
        if self._df is None:
            return

        col_idx = item.column()
        header = self._table.horizontalHeaderItem(col_idx)
        if not header:
            return
            
        column_name = header.text()
        
        if column_name in self._editable_columns:
            original_idx = item.data(Qt.ItemDataRole.UserRole)
            new_value = item.text()
            
            # CRITICAL: Only proceed if the value has actually changed.
            # This prevents hover background changes from triggering "edit" logic.
            current_val = str(coerce_cell(self._df.at[original_idx, column_name]))
            if new_value == current_val:
                return

            # Track this as a manual edit for visual highlighting
            self._manual_edits.add((original_idx, column_name))
            
            # Update internal item appearance immediately
            item.setForeground(QColor("#10B981"))
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            
            # Update the internal DataFrame so the edit persists across sorts/filters
            try:
                self._df.at[original_idx, column_name] = new_value
            except Exception as exc:
                print(f"DataTableWidget: Failed to update internal DF: {exc}")
                
            self.cell_changed.emit(original_idx, column_name, new_value)

    def _apply_filter(self, text: str) -> None:
        if self._df is None:
            return
        if not text.strip():
            self._render(self._df)
            return
        mask = self._df.astype(str).apply(
            lambda row: row.str.contains(text, case=False, na=False).any(),
            axis=1,
        )
        self._render(self._df[mask])