import pandas as pd
import pytest
from sheetguard.models.results import ProcessingResult, ValidationIssue, DuplicateGroup

def test_processing_result_drop_row():
    df = pd.DataFrame({
        "Name": ["A", "B", "C", "D"],
        "Val": [1, 2, 3, 4]
    })
    issues = [
        ValidationIssue(row_index=0, field_id="f", column="Name", severity="error", message="m0"),
        ValidationIssue(row_index=2, field_id="f", column="Name", severity="error", message="m2"),
        ValidationIssue(row_index=3, field_id="f", column="Name", severity="error", message="m3")
    ]
    duplicates = [
        DuplicateGroup(rule_name="r", key_values={}, row_indices=[0, 1, 2, 3])
    ]
    corrections = {
        (0, "Name"): "A1",
        (2, "Name"): "C1",
        (3, "Name"): "D1"
    }
    
    result = ProcessingResult(
        cleaned_df=df.copy(),
        original_df=df.copy(),
        issues=issues,
        duplicates=duplicates,
        corrections=corrections,
        summary={"total_rows": 4}
    )
    
    # Drop row at index 1 (B)
    result.drop_row(1)
    
    assert len(result.cleaned_df) == 3
    assert result.cleaned_df["Name"].tolist() == ["A", "C", "D"]
    assert result.summary["total_rows"] == 3
    
    # Issues at row 0 stay at 0
    # Issues at row 2 move to 1
    # Issues at row 3 move to 2
    assert len(result.issues) == 3
    assert result.issues[0].row_index == 0
    assert result.issues[1].row_index == 1
    assert result.issues[2].row_index == 2
    
    # Duplicate indices [0, 1, 2, 3] should become [0, 1, 2] (since 1 was dropped, 2->1, 3->2)
    assert len(result.duplicates) == 1
    assert result.duplicates[0].row_indices == [0, 1, 2]
    
    # Corrections (0, Name) stays
    # (2, Name) -> (1, Name)
    # (3, Name) -> (2, Name)
    assert (0, "Name") in result.corrections
    assert (1, "Name") in result.corrections
    assert (2, "Name") in result.corrections
    assert result.corrections[(1, "Name")] == "C1"

def test_processing_result_drop_row_remove_duplicate_group():
    df = pd.DataFrame({"A": [1, 1, 2]})
    duplicates = [DuplicateGroup(rule_name="r", key_values={}, row_indices=[0, 1])]
    result = ProcessingResult(cleaned_df=df, original_df=df, duplicates=duplicates)
    
    # Drop row 0, leaving only row 1 in the group. Group should be removed if < 2 rows.
    result.drop_row(0)
    assert len(result.duplicates) == 0
