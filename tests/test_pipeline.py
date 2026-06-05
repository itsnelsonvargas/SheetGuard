import pandas as pd
import pytest
from sheetguard.services.pipeline import ProcessingPipeline
from sheetguard.models.rules import RuleSet, ColumnRule

def test_pipeline_run():
    rule_set = RuleSet(
        rule_name="Pipeline Test",
        columns=[
            ColumnRule(field_id="name", column="Name", cleaning=["trim", "uppercase"], required=True),
            ColumnRule(field_id="age", column="Age", min_value=0)
        ]
    )
    
    df = pd.DataFrame({
        "Name": ["  john doe  ", ""],
        "Age": [25, -5]
    })
    
    pipeline = ProcessingPipeline(rule_set)
    progress_calls = []
    def progress_callback(pct, msg):
        progress_calls.append((pct, msg))
        
    result = pipeline.run(df, progress=progress_callback)
    
    # Check cleaning
    assert result.cleaned_df["Name"].iloc[0] == "JOHN DOE"
    
    # Check validation issues
    # 1. Row 1: empty name (required)
    # 2. Row 1: negative age (min_value)
    assert len(result.issues) == 2
    
    # Check summary
    assert result.summary["total_rows"] == 2
    assert result.summary["rule_name"] == "Pipeline Test"
    
    # Check progress calls
    assert len(progress_calls) > 0
    assert progress_calls[-1][0] == 100
