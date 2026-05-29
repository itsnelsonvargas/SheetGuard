"""Validation results and preview tabs."""

from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTabWidget, QVBoxLayout, QWidget

from sheetguard.gui.widgets.data_table import DataTableWidget
from sheetguard.gui.widgets.summary_cards import SummaryCards
from sheetguard.models.results import ProcessingResult

if TYPE_CHECKING:
    from sheetguard.models.rules import RuleSet


class ResultsView(QWidget):
    """Main results area: summary cards + tabbed tables."""

    request_row_deletion = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._result: ProcessingResult | None = None
        layout = QVBoxLayout(self)

        self.summary = SummaryCards()
        layout.addWidget(self.summary)

        self.tabs = QTabWidget()
        self.preview_table = DataTableWidget()
        self.summary_table = DataTableWidget()
        self.summary_table.set_sorting_enabled(False)
        self.errors_table = DataTableWidget()
        self.errors_table.set_editable_columns(["cleaned_value"])
        self.errors_table.cell_changed.connect(self._on_error_fixed)
        self.duplicates_table = DataTableWidget()

        self.tabs.addTab(self.preview_table, "Preview")
        self.tabs.addTab(self.errors_table, "Validation Errors")
        self.tabs.addTab(self.duplicates_table, "Duplicates")
        self.tabs.addTab(self.summary_table, "Summary")

        layout.addWidget(self.tabs)

    def _on_row_action(self, row_data: dict[str, Any]) -> None:
        if "row_number" in row_data:
            try:
                row_idx = int(row_data["row_number"]) - 1
                self.request_row_deletion.emit(row_idx)
            except (ValueError, TypeError):
                pass

    def show_result(self, result: ProcessingResult) -> None:
        self._result = result
        self.summary.update_counts(
            errors=result.error_count,
            warnings=result.warning_count,
            duplicates=len(result.duplicates),
            corrections=len(result.corrections),
        )
        self.preview_table.set_dataframe(result.cleaned_df)
        self.summary_table.set_dataframe(self._generate_column_summary(result.cleaned_df, result.rule_set))
        self.errors_table.set_dataframe(self._issues_df(result))
        self.duplicates_table.set_dataframe(
            self._duplicates_df(result), 
            action_column="Delete", 
            on_action=self._on_row_action
        )

    def show_preview(self, df: pd.DataFrame, rule_set: RuleSet | None = None) -> None:
        self.preview_table.set_dataframe(df)
        self.summary_table.set_dataframe(self._generate_column_summary(df, rule_set))

    def focus_preview_cell(self, row_index: int, column_name: str) -> bool:
        """Switch to the Preview tab and focus a specific row/column."""
        self.tabs.setCurrentWidget(self.preview_table)
        return self.preview_table.focus_cell(row_index, column_name)

    def _on_error_fixed(self, issue_df_idx: int, col_name: str, new_val: str) -> None:
        """Handle manual correction of a validation error from the errors table."""
        if not self._result or col_name != "cleaned_value":
            return

        try:
            # issue_df_idx is the original index in the issues list (from UserRole)
            issue = self._result.issues[issue_df_idx]
            row_idx = issue.row_index
            
            from sheetguard.utils.column_utils import resolve_column_name
            actual_col = resolve_column_name(self._result.cleaned_df, issue.column)
            
            # 1. Update the master Cleaned DataFrame
            self._result.cleaned_df.at[row_idx, actual_col] = new_val
            
            # 2. Update the issue object itself
            issue.cleaned_value = new_val
            
            # 3. Refresh Preview & Summary tabs
            # We don't refresh errors_table here because it already updated itself locally
            # and marked the cell as edited (green).
            self.preview_table.set_dataframe(self._result.cleaned_df)
            self.summary_table.set_dataframe(
                self._generate_column_summary(self._result.cleaned_df, self._result.rule_set)
            )
            
            # 4. Update status message
            main_win = self.window()
            if hasattr(main_win, "status"):
                main_win.status.showMessage(f"Manual correction saved for row {row_idx + 1}", 3000)
                
        except Exception as exc:
            import traceback
            traceback.print_exc()
            print(f"ResultsView: Failed to update manual correction: {exc}")

    def reset(self) -> None:
        self.summary.reset()
        self.preview_table.set_dataframe(None)
        self.summary_table.set_dataframe(None)
        self.errors_table.set_dataframe(None)
        self.duplicates_table.set_dataframe(None)

    @staticmethod
    def _generate_column_summary(df: pd.DataFrame, rule_set: RuleSet | None = None) -> pd.DataFrame:
        """Create a highly detailed summary table with categorized analytical metrics."""
        if df is None or df.empty:
            return pd.DataFrame()
        
        metrics_data = {}
        row_count = len(df)
        now = datetime.now()
        
        # Pre-resolve column rules for regex and lookups
        col_rules = {}
        if rule_set:
            from sheetguard.utils.column_utils import resolve_column_name
            for rule in rule_set.columns:
                try:
                    actual_name = resolve_column_name(df, rule.column)
                    col_rules[actual_name] = rule
                except (KeyError, ValueError):
                    continue

        # Structure categories
        categories = [
            ("CORE SUMMARY", ["Row Count", "Non-Empty Count", "Empty Count", "Unique Count", "Duplicate Count", "Null Percentage", "Most Common Value", "Least Common Value", "Distinct Ratio", "Uniqueness Density"]),
            ("NUMERIC ANALYSIS", ["Min", "Max", "Mean", "Median", "Mode", "Sum", "Standard Deviation", "Variance", "Negative Count", "Zero Count"]),
            ("DATE ANALYSIS", ["Earliest Date", "Latest Date", "Invalid Date Count", "Future Date Count", "Missing Date Count", "Age Distribution"]),
            ("TEXT ANALYSIS FUNCTIONS", ["Min Length", "Max Length", "Average Length", "Regex Match Count", "Uppercase Ratio", "Special Character Count", "Whitespace Issues", "Case Consistency"]),
            ("DATA QUALITY & VALIDATION", ["Duplicate Detection", "Invalid Format Count", "Outlier Detection", "Consistency Check", "Reference Match Rate"]),
            ("DATA TYPE DETECTION", ["Detected Type"])
        ]

        for col in df.columns:
            m = metrics_data[col] = {}
            try:
                series = df[col]
                s_str = series.astype(str)
                non_empty_mask = series.notna() & (s_str.str.strip().str.lower() != "nan") & (s_str.str.strip() != "")
                valid_series = series[non_empty_mask]
                non_empty = len(valid_series)
                empty = row_count - non_empty
                unique = valid_series.nunique()
                
                # --- 1. CORE SUMMARY ---
                value_counts = valid_series.value_counts()
                most_common = value_counts.index[0] if not value_counts.empty else "n/a"
                least_common = value_counts.index[-1] if not value_counts.empty else "n/a"
                null_pct = (empty / row_count * 100) if row_count > 0 else 0
                distinct_ratio = (unique / non_empty) if non_empty > 0 else 0
                uniqueness_density = (unique / row_count) if row_count > 0 else 0
                
                m["Row Count"] = row_count
                m["Non-Empty Count"] = non_empty
                m["Empty Count"] = empty
                m["Unique Count"] = unique
                m["Duplicate Count"] = non_empty - unique if non_empty > unique else 0
                m["Null Percentage"] = f"{null_pct:.2f}%"
                m["Most Common Value"] = most_common
                m["Least Common Value"] = least_common
                m["Distinct Ratio"] = f"{distinct_ratio:.4f}"
                m["Uniqueness Density"] = f"{uniqueness_density:.4f}"

                # --- 2. NUMERIC ANALYSIS ---
                num_series = pd.to_numeric(series, errors='coerce')
                valid_nums = num_series.dropna()
                if not valid_nums.empty:
                    try:
                        vf = valid_nums.astype(float)
                        m["Min"] = f"{vf.min():.2f}"
                        m["Max"] = f"{vf.max():.2f}"
                        m["Mean"] = f"{vf.mean():.2f}"
                        m["Median"] = f"{vf.median():.2f}"
                        
                        try:
                            m["Mode"] = f"{valid_nums.mode().iloc[0]:.2f}"
                        except Exception:
                            m["Mode"] = "n/a"
                            
                        m["Sum"] = f"{vf.sum():.2f}"
                        m["Standard Deviation"] = f"{vf.std():.4f}"
                        m["Variance"] = f"{vf.var():.4f}"
                        m["Negative Count"] = (vf < 0).sum()
                        m["Zero Count"] = (vf == 0).sum()
                        
                        # Outliers (Z-score > 3)
                        if len(vf) > 1 and vf.std() > 0:
                            z_scores = np.abs((vf - vf.mean()) / vf.std())
                            m["Outlier Detection"] = (z_scores > 3).sum()
                        else:
                            m["Outlier Detection"] = 0
                    except Exception as exc:
                        print(f"ResultsView: Numeric summary error for {col}: {exc}")
                        for k in ["Min", "Max", "Mean", "Median", "Mode", "Sum", "Standard Deviation", "Variance", "Negative Count", "Zero Count", "Outlier Detection"]:
                            m[k] = "error"
                else:
                    for k in ["Min", "Max", "Mean", "Median", "Mode", "Sum", "Standard Deviation", "Variance", "Negative Count", "Zero Count", "Outlier Detection"]:
                        m[k] = "n/a"

                # --- 3. DATE ANALYSIS ---
                date_series = pd.to_datetime(series, errors='coerce')
                valid_dates = date_series.dropna()
                if not valid_dates.empty:
                    m["Earliest Date"] = valid_dates.min().strftime("%Y-%m-%d")
                    m["Latest Date"] = valid_dates.max().strftime("%Y-%m-%d")
                    m["Invalid Date Count"] = (non_empty_mask & date_series.isna()).sum()
                    m["Future Date Count"] = (valid_dates > now).sum()
                    m["Missing Date Count"] = empty
                    # Age Distribution (if dates look like birthdays)
                    ages = (now - valid_dates).dt.days / 365.25
                    m["Age Distribution"] = f"{ages.min():.1f} - {ages.max():.1f} yrs"
                else:
                    for k in ["Earliest Date", "Latest Date", "Invalid Date Count", "Future Date Count", "Missing Date Count", "Age Distribution"]:
                        m[k] = "n/a"

                # --- 4. TEXT ANALYSIS ---
                valid_strings = valid_series.astype(str)
                if not valid_strings.empty:
                    lengths = valid_strings.str.len().astype(float)
                    m["Min Length"] = int(lengths.min())
                    m["Max Length"] = int(lengths.max())
                    m["Average Length"] = f"{lengths.mean():.2f}"
                    m["Whitespace Issues"] = (valid_strings != valid_strings.str.strip()).sum()
                    
                    is_upper = valid_strings.str.isupper().sum()
                    is_lower = valid_strings.str.islower().sum()
                    is_title = valid_strings.str.istitle().sum()
                    dom_count = max(is_upper, is_lower, is_title)
                    m["Case Consistency"] = f"{(dom_count / non_empty * 100):.1f}%"
                    
                    alpha_only = valid_strings.str.replace(r'[^a-zA-Z]', '', regex=True)
                    alpha_len = alpha_only.str.len().astype(float).sum()
                    upper_len = alpha_only.str.findall(r'[A-Z]').str.len().astype(float).sum()
                    m["Uppercase Ratio"] = f"{(upper_len / alpha_len if alpha_len > 0 else 0):.2f}"
                    
                    m["Special Character Count"] = valid_strings.str.replace(r'[a-zA-Z0-9\s]', '', regex=True).str.len().astype(float).sum()
                else:
                    for k in ["Min Length", "Max Length", "Average Length", "Whitespace Issues", "Case Consistency", "Uppercase Ratio", "Special Character Count"]:
                        m[k] = "n/a"

                # --- 5. DATA QUALITY & VALIDATION ---
                rule = col_rules.get(col)
                if rule and rule.regex:
                    try:
                        matches = valid_strings.str.match(rule.regex).sum()
                        m["Invalid Format Count"] = non_empty - matches
                        m["Regex Match Count"] = matches
                    except Exception:
                        m["Invalid Format Count"] = m["Regex Match Count"] = "error"
                else:
                    m["Invalid Format Count"] = m["Regex Match Count"] = "n/a"
                
                m["Duplicate Detection"] = "Found" if m["Duplicate Count"] > 0 else "None"
                m["Consistency Check"] = m["Case Consistency"]
                m["Reference Match Rate"] = "n/a" # Requires validator integration for actual rate

                # --- 6. DATA TYPE DETECTION ---
                if not valid_nums.empty and (valid_nums == valid_nums.astype(int)).all():
                    dtype = "Integer"
                elif not valid_nums.empty:
                    dtype = "Decimal"
                elif not valid_dates.empty:
                    dtype = "Date"
                elif unique <= 2 and non_empty > 0:
                    dtype = "Boolean"
                elif distinct_ratio < 0.05 and non_empty > 10:
                    dtype = "Categorical"
                else:
                    dtype = "Text"
                m["Detected Type"] = dtype
            except Exception as exc:
                print(f"ResultsView: Error generating summary for column '{col}': {exc}")
                for cat_name, keys in categories:
                    for k in keys:
                        if k not in m:
                            m[k] = "error"

        rows = []
        for cat_name, keys in categories:
            # Header
            h = {"Metric": cat_name}
            for c in df.columns: h[c] = None
            rows.append(h)
            # Metrics
            for k in keys:
                r = {"Metric": k}
                for c in df.columns: r[c] = metrics_data[c].get(k, "n/a")
                rows.append(r)

        return pd.DataFrame(rows)

    @staticmethod
    def _issues_df(result: ProcessingResult) -> pd.DataFrame:
        if not result.issues:
            return pd.DataFrame()
        return pd.DataFrame([i.to_dict() for i in result.issues])

    @staticmethod
    def _duplicates_df(result: ProcessingResult) -> pd.DataFrame:
        rows = []
        for g in result.duplicates:
            for idx in g.row_indices:
                row = result.cleaned_df.iloc[idx].to_dict()
                row["duplicate_rule"] = g.rule_name
                row["row_number"] = idx + 1
                rows.append(row)
        return pd.DataFrame(rows) if rows else pd.DataFrame()
