import pandas as pd
import pytest
from pathlib import Path
from sheetguard.core.exporter import WorkbookExporter
from sheetguard.models.results import ProcessingResult, ValidationIssue, DuplicateGroup

@pytest.fixture
def sample_result():
    df = pd.DataFrame({
        "Name": ["John Doe", "Jane Smith"],
        "Age": [30, 25]
    })
    issues = [
        ValidationIssue(row_index=0, field_id="name", column="Name", severity="warning", message="Test Warning"),
        ValidationIssue(row_index=1, field_id="age", column="Age", severity="error", message="Test Error")
    ]
    duplicates = [
        DuplicateGroup(rule_name="Test Rule", key_values={"Name": "John Doe"}, row_indices=[0, 1])
    ]
    corrections = {(0, "Name"): "JOHN DOE"}
    
    return ProcessingResult(
        cleaned_df=df,
        original_df=df.copy(),
        issues=issues,
        duplicates=duplicates,
        corrections=corrections,
        summary={"total_rows": 2}
    )

def test_workbook_exporter_full_report(tmp_path, sample_result):
    exporter = WorkbookExporter()
    path = tmp_path / "report.xlsx"
    exported_path = exporter.export_full_report(sample_result, path)
    
    assert exported_path.exists()
    # Basic check with pandas to see if we can read it back
    # (Checking if sheets exist)
    xl = pd.ExcelFile(exported_path)
    assert "CLEANED_DATA" in xl.sheet_names
    assert "VALIDATION_ERRORS" in xl.sheet_names
    assert "DUPLICATES" in xl.sheet_names
    assert "SUMMARY" in xl.sheet_names

def test_workbook_exporter_cleaned_only(tmp_path, sample_result):
    exporter = WorkbookExporter()
    path = tmp_path / "cleaned.xlsx"
    exported_path = exporter.export_cleaned_only(sample_result, path)
    
    assert exported_path.exists()
    xl = pd.ExcelFile(exported_path)
    assert "CLEANED_DATA" in xl.sheet_names
    assert len(xl.sheet_names) == 1

def test_workbook_exporter_autosize():
    # Smoke test for autosize
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["Short", "Very Long Column Header Name"])
    ws.append(["A", "B"])
    WorkbookExporter._autosize_columns(ws)
    assert ws.column_dimensions["B"].width > ws.column_dimensions["A"].width
