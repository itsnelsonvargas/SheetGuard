"""Visual rule builder dialog and panel."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sheetguard.core.rule_engine import RuleEngine
from sheetguard.models.rules import ColumnRule, DuplicateRule, RuleSet

CLEANING_OPTIONS = sorted(RuleEngine.SUPPORTED_CLEANING)


class ColumnRuleEditor(QDialog):
    """Edit a single column rule."""

    def __init__(self, rule: ColumnRule | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Column Rule")
        self.setMinimumWidth(480)
        self._rule = rule

        layout = QFormLayout(self)
        self.field_id = QTextEdit()
        self.field_id.setMaximumHeight(32)
        self.field_id.setPlainText(rule.field_id if rule else "")
        self.column = QTextEdit()
        self.column.setMaximumHeight(32)
        self.column.setPlainText(rule.column if rule else "")
        self.required = QCheckBox("Required")
        self.required.setChecked(rule.required if rule else False)
        self.warning_only = QCheckBox("Warning only")
        self.warning_only.setChecked(rule.warning_only if rule else False)

        self.cleaning = QListWidget()
        self.cleaning.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for op in CLEANING_OPTIONS:
            item = QListWidgetItem(op)
            self.cleaning.addItem(item)
            if rule and op in rule.cleaning:
                item.setSelected(True)

        self.allowed_values = QTextEdit()
        self.allowed_values.setPlaceholderText("Comma-separated: M, F")
        if rule and rule.allowed_values:
            self.allowed_values.setPlainText(", ".join(rule.allowed_values))

        self.regex = QTextEdit()
        self.regex.setMaximumHeight(32)
        if rule and rule.regex:
            self.regex.setPlainText(rule.regex)

        self.min_length = QSpinBox()
        self.min_length.setRange(0, 9999)
        self.max_length = QSpinBox()
        self.max_length.setRange(0, 9999)
        if rule and rule.min_length:
            self.min_length.setValue(rule.min_length)
        if rule and rule.max_length:
            self.max_length.setValue(rule.max_length)

        self.lookup = QComboBox()
        self.lookup.setEditable(True)
        if rule and rule.lookup:
            self.lookup.setCurrentText(rule.lookup)

        layout.addRow("Field ID", self.field_id)
        layout.addRow("Column (letter or name)", self.column)
        layout.addRow(self.required)
        layout.addRow(self.warning_only)
        layout.addRow("Cleaning ops", self.cleaning)
        layout.addRow("Allowed values", self.allowed_values)
        layout.addRow("Regex", self.regex)
        layout.addRow("Min length", self.min_length)
        layout.addRow("Max length", self.max_length)
        layout.addRow("Lookup name", self.lookup)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_rule(self) -> ColumnRule | None:
        fid = self.field_id.toPlainText().strip()
        col = self.column.toPlainText().strip()
        if not fid or not col:
            return None
        allowed_raw = self.allowed_values.toPlainText().strip()
        allowed = [v.strip() for v in allowed_raw.split(",") if v.strip()] if allowed_raw else None
        cleaning = [
            self.cleaning.item(i).text()
            for i in range(self.cleaning.count())
            if self.cleaning.item(i).isSelected()
        ]
        return ColumnRule(
            field_id=fid,
            column=col,
            required=self.required.isChecked(),
            warning_only=self.warning_only.isChecked(),
            cleaning=cleaning,
            allowed_values=allowed,
            regex=self.regex.toPlainText().strip() or None,
            min_length=self.min_length.value() if self.min_length.value() > 0 else None,
            max_length=self.max_length.value() if self.max_length.value() > 0 else None,
            lookup=self.lookup.currentText().strip() or None,
        )


class RuleBuilderPanel(QWidget):
    """Sidebar panel for building and editing rule sets."""

    rule_changed = Signal(object)
    rule_saved = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rule_set: RuleSet | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Rule Builder"))

        meta = QGroupBox("Rule Set")
        meta_layout = QFormLayout(meta)
        self.rule_name = QTextEdit()
        self.rule_name.setMaximumHeight(32)
        meta_layout.addRow("Name", self.rule_name)
        layout.addWidget(meta)

        self.column_list = QListWidget()
        layout.addWidget(QLabel("Columns"))
        layout.addWidget(self.column_list)

        col_btns = QHBoxLayout()
        self.btn_add_col = QPushButton("➕ Add")
        self.btn_add_col.setObjectName("success")
        self.btn_edit_col = QPushButton("✏️ Edit")
        self.btn_del_col = QPushButton("🗑️ Delete")
        self.btn_del_col.setObjectName("danger")
        self.btn_up_col = QPushButton("🔼 Up")
        self.btn_down_col = QPushButton("🔽 Down")
        for b in (self.btn_add_col, self.btn_edit_col, self.btn_del_col, self.btn_up_col, self.btn_down_col):
            col_btns.addWidget(b)
        layout.addLayout(col_btns)

        dup_group = QGroupBox("Duplicate Rules")
        dup_layout = QVBoxLayout(dup_group)
        self.dup_list = QListWidget()
        dup_layout.addWidget(self.dup_list)
        dup_btns = QHBoxLayout()
        self.btn_add_dup = QPushButton("➕ Add Dup Rule")
        self.btn_add_dup.setObjectName("success")
        self.btn_del_dup = QPushButton("🗑️ Remove")
        self.btn_del_dup.setObjectName("danger")
        dup_btns.addWidget(self.btn_add_dup)
        dup_btns.addWidget(self.btn_del_dup)
        dup_layout.addLayout(dup_btns)
        layout.addWidget(dup_group)

        save_row = QHBoxLayout()
        self.btn_save = QPushButton("💾 Save Rule Set")
        self.btn_new = QPushButton("📄 New")
        save_row.addWidget(self.btn_new)
        save_row.addWidget(self.btn_save)
        layout.addLayout(save_row)

        self.btn_add_col.clicked.connect(self._add_column)
        self.btn_edit_col.clicked.connect(self._edit_column)
        self.btn_del_col.clicked.connect(self._delete_column)
        self.btn_up_col.clicked.connect(lambda: self._move_column(-1))
        self.btn_down_col.clicked.connect(lambda: self._move_column(1))
        self.btn_add_dup.clicked.connect(self._add_duplicate_rule)
        self.btn_del_dup.clicked.connect(self._delete_duplicate_rule)
        self.btn_save.clicked.connect(self._save_rule_set)
        self.btn_new.clicked.connect(self._new_rule_set)

    def load_rule_set(self, rule_set: RuleSet | None) -> None:
        self._rule_set = rule_set
        if not rule_set:
            self.rule_name.clear()
            self.column_list.clear()
            self.dup_list.clear()
            return
        self.rule_name.setPlainText(rule_set.rule_name)
        self._refresh_lists()
        self.rule_changed.emit(rule_set)

    def get_rule_set(self) -> RuleSet | None:
        if not self._rule_set:
            return None
        self._rule_set.rule_name = self.rule_name.toPlainText().strip() or "Untitled"
        return self._rule_set

    def _refresh_lists(self) -> None:
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
            self.dup_list.addItem(f"{dup.name}: {' + '.join(dup.fields)}")

    def _new_rule_set(self) -> None:
        self._rule_set = RuleSet(rule_name="New Rule Set", version="1.0", columns=[])
        self.load_rule_set(self._rule_set)

    def _add_column(self) -> None:
        if not self._rule_set:
            self._new_rule_set()
        dlg = ColumnRuleEditor(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            rule = dlg.get_rule()
            if rule:
                self._rule_set.columns.append(rule)
                self._refresh_lists()
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
            self._refresh_lists()
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
            return
        name, ok = QInputDialog.getText(self, "Duplicate Rule", "Rule name:")
        if not ok or not name:
            return
        fields, ok2 = QInputDialog.getText(self, "Fields", "Field IDs (comma-separated):")
        if not ok2 or not fields:
            return
        field_list = [f.strip() for f in fields.split(",") if f.strip()]
        self._rule_set.duplicate_rules.append(DuplicateRule(name=name, fields=field_list))
        self._refresh_lists()
        self.rule_changed.emit(self._rule_set)

    def _delete_duplicate_rule(self) -> None:
        idx = self.dup_list.currentRow()
        if self._rule_set and idx >= 0:
            del self._rule_set.duplicate_rules[idx]
            self._refresh_lists()
            self.rule_changed.emit(self._rule_set)

    def _save_rule_set(self) -> None:
        rs = self.get_rule_set()
        if not rs:
            QMessageBox.warning(self, "Save", "No rule set to save.")
            return
        try:
            RuleEngine.validate(rs)
            from sheetguard.services.rule_service import RuleService

            path = RuleService().save_to_library(rs)
            self.rule_saved.emit()
            QMessageBox.information(self, "Saved", f"Rule set saved to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
