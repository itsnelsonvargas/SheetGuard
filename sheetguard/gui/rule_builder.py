"""Visual rule builder dialog and panel."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sheetguard.core.rule_engine import RuleEngine
from sheetguard.models.rules import ColumnRule, DuplicateRule, LookupSource, RuleSet
from sheetguard.services.lookup_service import LookupService

CLEANING_DESCRIPTIONS = {
    "trim": "Remove leading/trailing spaces",
    "collapse_spaces": "Fix double/multiple spaces",
    "uppercase": "CONVERT TO ALL CAPS",
    "lowercase": "convert to all lowercase",
    "title": "Convert To Title Case",
    "pascal_case": "Convert To PascalCase",
    "remove_special": "Remove symbols (!@#$, etc.)",
    "normalize_date": "Standardize date formats",
    "numeric_cleanup": "Keep only numbers/decimals",
}

CLEANING_OPTIONS = sorted(RuleEngine.SUPPORTED_CLEANING)


class ColumnRuleEditor(QDialog):
    """Edit a single column rule with improved UI/UX."""

    def __init__(self, rule: ColumnRule | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Column Rule")
        self.setMinimumWidth(900)  # Stretch to width
        self._rule = rule

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # Content area with two columns
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # --- LEFT COLUMN (ID & Cleaning) ---
        left_col = QVBoxLayout()
        left_col.setSpacing(15)

        # 1. Identification Section
        id_group = QGroupBox("1. Identification")
        id_layout = QFormLayout(id_group)
        
        self.field_id = QLineEdit()
        self.field_id.setPlaceholderText("e.g., Learner Name, Date of Birth")
        self.field_id.setText(rule.field_id if rule else "")
        id_layout.addRow("Display Name:", self.field_id)
        
        id_help = QLabel("The descriptive name used in reports.")
        id_help.setStyleSheet("color: #64748B; font-size: 11px;")
        id_layout.addRow("", id_help)

        self.column = QLineEdit()
        self.column.setPlaceholderText("e.g., A, B or Header Name")
        self.column.setText(rule.column if rule else "")
        id_layout.addRow("Excel Column:", self.column)
        
        col_help = QLabel("Letter (A, B) or exact header name in the sheet.")
        col_help.setStyleSheet("color: #64748B; font-size: 11px;")
        id_layout.addRow("", col_help)

        left_col.addWidget(id_group)

        # 2. Cleaning Section
        clean_group = QGroupBox("2. Automatic Data Cleaning")
        clean_layout = QVBoxLayout(clean_group)
        
        clean_desc = QLabel("Fix common typos automatically before validation.")
        clean_desc.setStyleSheet("font-weight: 600; color: #1E293B;")
        clean_layout.addWidget(clean_desc)

        # Define casing options for mutual exclusion
        self._casing_ops = {"uppercase", "lowercase", "title", "pascal_case"}

        # Create a grid of checkboxes for cleaning options
        self._clean_checkboxes: dict[str, QCheckBox] = {}
        grid_container = QWidget()
        grid = QGridLayout(grid_container)
        grid.setContentsMargins(0, 5, 0, 0)
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(8)

        for i, op in enumerate(CLEANING_OPTIONS):
            row = i // 2
            col = i % 2
            
            cb = QCheckBox(op.replace("_", " ").title())
            cb.setToolTip(CLEANING_DESCRIPTIONS.get(op, ""))
            if rule and op in rule.cleaning:
                cb.setChecked(True)
            self._clean_checkboxes[op] = cb
            
            if op in self._casing_ops:
                cb.toggled.connect(lambda checked, o=op: self._on_casing_toggled(checked, o))
            
            desc_label = QLabel(f"<i>{CLEANING_DESCRIPTIONS.get(op, '')}</i>")
            desc_label.setStyleSheet("color: #64748B; font-size: 10px;")
            
            cell_layout = QVBoxLayout()
            cell_layout.setSpacing(1)
            cell_layout.addWidget(cb)
            cell_layout.addWidget(desc_label)
            grid.addLayout(cell_layout, row, col)

        clean_layout.addWidget(grid_container)
        left_col.addWidget(clean_group)
        left_col.addStretch()
        content_layout.addLayout(left_col, 4)

        # --- RIGHT COLUMN (Validation) ---
        right_col = QVBoxLayout()
        right_col.setSpacing(15)

        # 3. Validation Section
        val_group = QGroupBox("3. Validation Rules (Constraints)")
        val_layout = QFormLayout(val_group)
        val_layout.setSpacing(12)

        # Status checkboxes
        self.required = QCheckBox("Field cannot be empty")
        self.required.setToolTip("If checked, empty cells will be flagged as errors.")
        self.required.setChecked(rule.required if rule else False)
        val_layout.addRow("Requirement:", self.required)

        self.validate_email = QCheckBox("Must be a valid Email")
        self.validate_email.setToolTip("Value must follow standard email format (user@example.com).")
        self.validate_email.setChecked(rule.validate_email if rule else False)
        val_layout.addRow("Email Check:", self.validate_email)

        self.warning_only = QCheckBox("Report issues as Warnings only")
        self.warning_only.setToolTip("If checked, failures will be Warnings instead of Errors.")
        self.warning_only.setChecked(rule.warning_only if rule else False)
        val_layout.addRow("Severity:", self.warning_only)
        
        severity_help = QLabel("<b>Error:</b> Data is broken. <br><b>Warning:</b> Data is suspicious.")
        severity_help.setStyleSheet("color: #64748B; font-size: 11px;")
        val_layout.addRow("", severity_help)

        # Lengths
        len_layout = QHBoxLayout()
        self.min_length = QSpinBox()
        self.min_length.setRange(0, 9999)
        self.min_length.setMinimumWidth(100)
        self.max_length = QSpinBox()
        self.max_length.setRange(0, 9999)
        self.max_length.setMinimumWidth(100)
        if rule and rule.min_length:
            self.min_length.setValue(rule.min_length)
        if rule and rule.max_length:
            self.max_length.setValue(rule.max_length)
        len_layout.addWidget(QLabel("Min:"))
        len_layout.addWidget(self.min_length)
        len_layout.addWidget(QLabel("Max:"))
        len_layout.addWidget(self.max_length)
        val_layout.addRow("Text Length:", len_layout)

        # Values & Patterns
        self.allowed_values = QLineEdit()
        self.allowed_values.setPlaceholderText("e.g., M, F, Other")
        if rule and rule.allowed_values:
            self.allowed_values.setText(", ".join(rule.allowed_values))
        val_layout.addRow("Allowed List:", self.allowed_values)

        self.regex = QLineEdit()
        self.regex.setPlaceholderText("e.g., ^[0-9]{12}$")
        if rule and rule.regex:
            self.regex.setText(rule.regex)
        val_layout.addRow("Pattern (Regex):", self.regex)

        self.lookup = QComboBox()
        self.lookup.setEditable(True)
        self.lookup.setPlaceholderText("Search reference lists...")
        
        # Populate with saved lookups
        try:
            ls = LookupService()
            entries = ls.list_entries()
            for entry in entries:
                self.lookup.addItem(entry.name)
        except Exception:
            pass

        if rule and rule.lookup:
            self.lookup.setCurrentText(rule.lookup)
        val_layout.addRow("Lookup Table:", self.lookup)

        right_col.addWidget(val_group)
        right_col.addStretch()
        content_layout.addLayout(right_col, 5)

        main_layout.addLayout(content_layout)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def _on_casing_toggled(self, checked: bool, op: str) -> None:
        """Ensure only one casing option is selected at a time."""
        if not checked:
            return
            
        # Uncheck all other casing options
        for other_op in self._casing_ops:
            if other_op != op and other_op in self._clean_checkboxes:
                self._clean_checkboxes[other_op].blockSignals(True)
                self._clean_checkboxes[other_op].setChecked(False)
                self._clean_checkboxes[other_op].blockSignals(False)

    def get_rule(self) -> ColumnRule | None:
        fid = self.field_id.text().strip()
        col = self.column.text().strip()
        if not fid or not col:
            return None
        allowed_raw = self.allowed_values.text().strip()
        allowed = [v.strip() for v in allowed_raw.split(",") if v.strip()] if allowed_raw else None
        
        cleaning = [
            op for op, cb in self._clean_checkboxes.items() if cb.isChecked()
        ]
        
        return ColumnRule(
            field_id=fid,
            column=col,
            required=self.required.isChecked(),
            warning_only=self.warning_only.isChecked(),
            cleaning=cleaning,
            allowed_values=allowed,
            regex=self.regex.text().strip() or None,
            min_length=self.min_length.value() if self.min_length.value() > 0 else None,
            max_length=self.max_length.value() if self.max_length.value() > 0 else None,
            lookup=self.lookup.currentText().strip() or None,
            validate_email=self.validate_email.isChecked(),
        )


class DuplicateRuleEditor(QDialog):
    """Edit a duplicate detection rule."""

    def __init__(self, rule: DuplicateRule | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Duplicate Rule")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name = QLineEdit()
        self.name.setPlaceholderText("e.g., Patient Identity, Address Check")
        self.name.setText(rule.name if rule else "")
        form.addRow("Rule Name:", self.name)

        self.fields = QLineEdit()
        self.fields.setPlaceholderText("Column names or IDs, separated by commas")
        if rule:
            self.fields.setText(", ".join(rule.fields))
        form.addRow("Match Fields:", self.fields)

        self.match_mode = QComboBox()
        self.match_mode.addItems(["exact", "fuzzy"])
        if rule:
            self.match_mode.setCurrentText(rule.match_mode)
        form.addRow("Match Mode:", self.match_mode)

        self.threshold = QSpinBox()
        self.threshold.setRange(50, 100)
        self.threshold.setSuffix("%")
        self.threshold.setValue(int(rule.fuzzy_threshold) if rule else 90)
        self.threshold.setEnabled(self.match_mode.currentText() == "fuzzy")
        form.addRow("Fuzzy Threshold:", self.threshold)

        self.match_mode.currentTextChanged.connect(
            lambda t: self.threshold.setEnabled(t == "fuzzy")
        )

        layout.addLayout(form)

        help_text = QLabel(
            "<small><b>Exact:</b> Rows must match perfectly after trimming.<br>"
            "<b>Fuzzy:</b> Rows match if they are very similar (typos allowed).</small>"
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #64748B;")
        layout.addWidget(help_text)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_rule(self) -> DuplicateRule | None:
        name = self.name.text().strip()
        fields_raw = self.fields.text().strip()
        if not name or not fields_raw:
            return None
        
        field_list = [f.strip() for f in fields_raw.split(",") if f.strip()]
        return DuplicateRule(
            name=name,
            fields=field_list,
            match_mode=self.match_mode.currentText(),
            fuzzy_threshold=float(self.threshold.value()),
        )


class RuleBuilderPanel(QWidget):
    """Sidebar panel for building and editing rule sets (Compact Ultra Edition)."""

    rule_changed = Signal(object)
    rule_saved = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rule_set: RuleSet | None = None
        self._current_path: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 1. Rule Set Header (Compact)
        self.rule_name_label = QLabel("Untitled")
        self.rule_name_label.setStyleSheet("font-weight: 800; font-size: 13px; color: #00D4FF;")
        self.rule_name_label.setWordWrap(True)
        
        self.btn_rename = QPushButton("✏️")
        self.btn_rename.setFixedSize(26, 26)
        self.btn_rename.setObjectName("actionSecondary")
        
        name_row = QHBoxLayout()
        name_row.addWidget(self.rule_name_label)
        name_row.addStretch()
        name_row.addWidget(self.btn_rename)
        layout.addLayout(name_row)

        # 2. Columns List (Compact)
        lbl_cols = QLabel("COLUMNS")
        lbl_cols.setObjectName("groupHeader")
        lbl_cols.setWordWrap(True)
        layout.addWidget(lbl_cols)
        
        self.column_list = QListWidget()
        self.column_list.setObjectName("ruleColumns")
        self.column_list.setMinimumHeight(80)
        self.column_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.column_list, stretch=1)

        col_btns = QHBoxLayout()
        col_btns.setSpacing(5)
        self.btn_add_col = QPushButton("+ Add")
        self.btn_edit_col = QPushButton("Edit")
        self.btn_del_col = QPushButton("Del")
        self.btn_del_col.setObjectName("deleteAction")
        for b in (self.btn_add_col, self.btn_edit_col, self.btn_del_col):
            b.setObjectName("actionSecondary") if b != self.btn_del_col else None
            b.setMinimumHeight(28)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            col_btns.addWidget(b, stretch=1)
        layout.addLayout(col_btns)

        # 3. Duplicate Rules (Compact)
        lbl_dups = QLabel("DUPLICATE RULES")
        lbl_dups.setObjectName("groupHeader")
        lbl_dups.setWordWrap(True)
        layout.addWidget(lbl_dups)

        self.dup_list = QListWidget()
        self.dup_list.setObjectName("duplicateRules")
        self.dup_list.setMinimumHeight(60)
        self.dup_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.dup_list, stretch=1)
        
        dup_btns = QHBoxLayout()
        dup_btns.setSpacing(5)
        self.btn_add_dup = QPushButton("+ Dup")
        self.btn_edit_dup = QPushButton("Edit")
        self.btn_import_dup = QPushButton("Import")
        self.btn_import_dup.setToolTip("Import duplicate rules from a JSON file")
        self.btn_export_dup = QPushButton("Export")
        self.btn_export_dup.setToolTip("Export selected duplicate rule to a JSON file")
        self.btn_del_dup = QPushButton("Del")
        self.btn_del_dup.setObjectName("deleteAction")
        for b in (self.btn_add_dup, self.btn_edit_dup, self.btn_import_dup, self.btn_export_dup, self.btn_del_dup):
            b.setObjectName("actionSecondary") if b != self.btn_del_dup else None
            b.setMinimumHeight(28)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            dup_btns.addWidget(b, stretch=1)
        layout.addLayout(dup_btns)

        # 4. Save/New Actions
        layout.addSpacing(5)
        save_row = QHBoxLayout()
        self.btn_save = QPushButton("💾 Save Rule Set")
        self.btn_save.setObjectName("primary")
        self.btn_save.setMinimumHeight(34)
        self.btn_save.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_new = QPushButton("📄 New")
        self.btn_new.setObjectName("actionSecondary")
        self.btn_new.setMinimumHeight(34)
        self.btn_new.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        save_row.addWidget(self.btn_new, stretch=1)
        save_row.addWidget(self.btn_save, stretch=1)
        layout.addLayout(save_row)

        self.btn_add_col.clicked.connect(self._add_column)
        self.btn_edit_col.clicked.connect(self._edit_column)
        self.btn_del_col.clicked.connect(self._delete_column)
        self.btn_add_dup.clicked.connect(self._add_duplicate_rule)
        self.btn_edit_dup.clicked.connect(self._edit_duplicate_rule)
        self.btn_import_dup.clicked.connect(self._import_duplicate_rules)
        self.btn_export_dup.clicked.connect(self._export_duplicate_rule)
        self.btn_del_dup.clicked.connect(self._delete_duplicate_rule)
        self.btn_rename.clicked.connect(self._rename_rule_set)
        self.btn_save.clicked.connect(self._save_rule_set)
        self.btn_new.clicked.connect(self._new_rule_set)

    def _rename_rule_set(self) -> None:
        """Prompt the user to rename the current rule set."""
        if not self._rule_set:
            return
            
        new_name, ok = QInputDialog.getText(
            self, "Rename Rule Set", "New Name:", 
            text=self.rule_name_label.text()
        )
        if ok and new_name.strip():
            self.rule_name_label.setText(new_name.strip())
            self._rule_set.rule_name = new_name.strip()
            self.rule_changed.emit(self._rule_set)
            self._save_rule_set()

    def load_rule_set(self, rule_set: RuleSet | None, path: str | None = None) -> None:
        self._rule_set = rule_set
        self._current_path = path
        if not rule_set:
            self.rule_name_label.setText("None")
            self.column_list.clear()
            self.dup_list.clear()
            return
        self.rule_name_label.setText(rule_set.rule_name)
        self._refresh_lists()
        self.rule_changed.emit(rule_set)

    def get_rule_set(self) -> RuleSet | None:
        if not self._rule_set:
            return None
        self._rule_set.rule_name = self.rule_name_label.text()
        self._sync_lookups()
        return self._rule_set

    def _sync_lookups(self) -> None:
        """Resolve named lookups from the library into LookupSource objects."""
        if not self._rule_set:
            return

        lookup_names = {c.lookup for c in self._rule_set.columns if c.lookup}
        from sheetguard.services.lookup_service import LookupService
        ls = LookupService()
        entries = {e.name: e for e in ls.list_entries()}

        new_lookups = []
        for name in lookup_names:
            if name in entries:
                meta = entries[name]
                new_lookups.append(
                    LookupSource(
                        name=meta.name,
                        path=meta.stored_path,
                        key_column=meta.key_column,
                        match_mode=meta.match_mode,
                        fuzzy_threshold=meta.fuzzy_threshold,
                    )
                )
            else:
                # Keep existing if manually configured or if it doesn't exist in library
                existing = next((l for l in self._rule_set.lookups if l.name == name), None)
                if existing:
                    new_lookups.append(existing)
                else:
                    # Create a placeholder if it's just a name
                    new_lookups.append(LookupSource(name=name, path=name, key_column="0"))

        self._rule_set.lookups = new_lookups

    def _refresh_lists(
        self,
        selected_column_row: int | None = None,
        selected_dup_row: int | None = None,
    ) -> None:
        if selected_column_row is None:
            selected_column_row = self.column_list.currentRow()
        if selected_dup_row is None:
            selected_dup_row = self.dup_list.currentRow()

        self.column_list.clear()
        self.dup_list.clear()
        if not self._rule_set:
            return
        for col in self._rule_set.columns:
            flags = []
            if col.required:
                flags.append("req")
            if col.cleaning:
                flags.append(",".join(col.cleaning))
            suffix = f" [{', '.join(flags)}]" if flags else ""
            self.column_list.addItem(f"{col.field_id} → {col.column}{suffix}")
        for dup in self._rule_set.duplicate_rules:
            mode = " (Fuzzy)" if dup.match_mode == "fuzzy" else ""
            self.dup_list.addItem(f"{dup.name}{mode}: {' + '.join(dup.fields)}")

        if self.column_list.count() and selected_column_row >= 0:
            self.column_list.setCurrentRow(min(selected_column_row, self.column_list.count() - 1))
        if self.dup_list.count() and selected_dup_row >= 0:
            self.dup_list.setCurrentRow(min(selected_dup_row, self.dup_list.count() - 1))

    def _new_rule_set(self) -> None:
        self._rule_set = RuleSet(rule_name="New Rule Set", columns=[])
        self.load_rule_set(self._rule_set)

    def _add_column(self) -> None:
        if not self._rule_set:
            self._new_rule_set()
        dlg = ColumnRuleEditor(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            rule = dlg.get_rule()
            if rule:
                self._rule_set.columns.append(rule)
                self._refresh_lists(selected_column_row=len(self._rule_set.columns) - 1)
                self.rule_changed.emit(self._rule_set)

    def _edit_column(self) -> None:
        idx = self.column_list.currentRow()
        if self._rule_set is None or idx < 0:
            return
        dlg = ColumnRuleEditor(self._rule_set.columns[idx], parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            rule = dlg.get_rule()
            if rule:
                self._rule_set.columns[idx] = rule
                self._refresh_lists()
                self.rule_changed.emit(self._rule_set)

    def _delete_column(self) -> None:
        idx = self.column_list.currentRow()
        if self._rule_set and idx >= 0:
            del self._rule_set.columns[idx]
            self._refresh_lists(selected_column_row=idx)
            self.rule_changed.emit(self._rule_set)

    def _move_column(self, direction: int) -> None:
        idx = self.column_list.currentRow()
        if self._rule_set is None or idx < 0:
            return
        new_idx = idx + direction
        if 0 <= new_idx < len(self._rule_set.columns):
            cols = self._rule_set.columns
            cols[idx], cols[new_idx] = cols[new_idx], cols[idx]
            self._refresh_lists()
            self.column_list.setCurrentRow(new_idx)
            self.rule_changed.emit(self._rule_set)

    def _add_duplicate_rule(self) -> None:
        if not self._rule_set:
            self._new_rule_set()
        dlg = DuplicateRuleEditor(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            rule = dlg.get_rule()
            if rule:
                self._rule_set.duplicate_rules.append(rule)
                self._refresh_lists(selected_dup_row=len(self._rule_set.duplicate_rules) - 1)
                self.rule_changed.emit(self._rule_set)

    def _edit_duplicate_rule(self) -> None:
        idx = self.dup_list.currentRow()
        if self._rule_set is None or idx < 0:
            return
        dlg = DuplicateRuleEditor(self._rule_set.duplicate_rules[idx], parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            rule = dlg.get_rule()
            if rule:
                self._rule_set.duplicate_rules[idx] = rule
                self._refresh_lists()
                self.rule_changed.emit(self._rule_set)

    def _delete_duplicate_rule(self) -> None:
        idx = self.dup_list.currentRow()
        if self._rule_set and idx >= 0:
            del self._rule_set.duplicate_rules[idx]
            self._refresh_lists(selected_dup_row=idx)
            self.rule_changed.emit(self._rule_set)

    def _import_duplicate_rules(self) -> None:
        """Import duplicate rules from a JSON file."""
        if not self._rule_set:
            self._new_rule_set()

        path, _ = QFileDialog.getOpenFileName(
            self, "Import Duplicate Rule", "", "JSON Files (*.json)"
        )
        if not path:
            return

        try:
            import json
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                for item in data:
                    self._rule_set.duplicate_rules.append(DuplicateRule.from_dict(item))
            else:
                self._rule_set.duplicate_rules.append(DuplicateRule.from_dict(data))

            self._refresh_lists()
            self.rule_changed.emit(self._rule_set)
            QMessageBox.information(self, "Import", "Duplicate rule(s) imported successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import: {str(e)}")

    def _export_duplicate_rule(self) -> None:
        """Export the selected duplicate rule to a JSON file."""
        idx = self.dup_list.currentRow()
        if self._rule_set is None or idx < 0:
            QMessageBox.warning(self, "Export", "Select a duplicate rule to export.")
            return

        rule = self._rule_set.duplicate_rules[idx]
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Duplicate Rule", f"{rule.name}.json", "JSON Files (*.json)"
        )
        if not path:
            return

        try:
            import json
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rule.to_dict(), f, indent=2)
            QMessageBox.information(self, "Export", "Duplicate rule exported successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")

    def _save_rule_set(self) -> None:
        rs = self.get_rule_set()
        if not rs:
            QMessageBox.warning(self, "Save", "No rule set to save.")
            return
        try:
            RuleEngine.validate(rs)
            from sheetguard.services.rule_service import RuleService

            # Use old_path to handle renaming (actual move/delete)
            path = RuleService().save_to_library(rs, old_path=self._current_path)
            self._current_path = str(path)
            self.rule_saved.emit(self._current_path)
            QMessageBox.information(self, "Saved", f"Rule set saved to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
