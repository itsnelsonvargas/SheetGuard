import pandas as pd
import pytest
from sheetguard.core.cleaner import DataCleaner
from sheetguard.models.rules import RuleSet, ColumnRule

@pytest.fixture
def cleaning_rule_set():
    return RuleSet(
        rule_name="Test Cleaner",
        columns=[
            ColumnRule(field_id="name", column="Name", cleaning=["trim", "uppercase", "collapse_spaces"]),
            ColumnRule(field_id="code", column="Code", cleaning=["remove_special"]),
            ColumnRule(field_id="amount", column="Amount", cleaning=["numeric_cleanup"]),
            ColumnRule(field_id="date", column="Date", cleaning=["normalize_date"]),
            ColumnRule(field_id="ref", column="Ref", cleaning=["pascal_case"])
        ]
    )

def test_cleaner_basic_ops(cleaning_rule_set):
    df = pd.DataFrame({
        "Name": ["  john   doe  ", "jane smith"],
        "Code": ["ABC-123!", "DEF#456"],
        "Amount": ["1,234.50", "$ 100"],
        "Date": ["01/01/2023", "2023-12-25"],
        "Ref": ["hello world", "foo-bar_baz"]
    })
    
    cleaner = DataCleaner(cleaning_rule_set)
    cleaned_df = cleaner.clean(df)
    
    assert cleaned_df["Name"].iloc[0] == "JOHN DOE"
    assert cleaned_df["Name"].iloc[1] == "JANE SMITH"
    
    assert cleaned_df["Code"].iloc[0] == "ABC-123" # - is not removed by [^\w\s\-\.\@]
    assert cleaned_df["Code"].iloc[1] == "DEF456"
    
    assert cleaned_df["Amount"].iloc[0] == 1234.5
    assert cleaned_df["Amount"].iloc[1] == 100
    
    assert cleaned_df["Date"].iloc[0] == "2023-01-01"
    assert cleaned_df["Date"].iloc[1] == "2023-12-25"
    
    assert cleaned_df["Ref"].iloc[0] == "HelloWorld"
    assert cleaned_df["Ref"].iloc[1] == "FooBarBaz"

def test_cleaner_corrections(cleaning_rule_set):
    df = pd.DataFrame({
        "Name": ["Already Clean", "  needs trim  "],
        "Code": ["X", "X"],
        "Amount": ["1", "1"],
        "Date": ["2023-01-01", "2023-01-01"],
        "Ref": ["X", "X"]
    })
    
    cleaner = DataCleaner(cleaning_rule_set)
    cleaner.clean(df)
    
    # "Already Clean" -> "ALREADY CLEAN" (changed)
    # "  needs trim  " -> "NEEDS TRIM" (changed)
    assert len(cleaner.corrections) == 2
    assert cleaner.corrections[(1, "Name")] == "NEEDS TRIM"

def test_cleaner_is_empty():
    assert DataCleaner._is_empty(None) is True
    assert DataCleaner._is_empty(float("nan")) is True
    assert DataCleaner._is_empty("  ") is True
    assert DataCleaner._is_empty("abc") is False

def test_numeric_cleanup_extra():
    assert DataCleaner._numeric_cleanup("1,234,567.89") == 1234567.89
    assert DataCleaner._numeric_cleanup("123.00") == 123
    assert DataCleaner._numeric_cleanup("not a number") == "not a number"
    assert DataCleaner._numeric_cleanup("abc 123 def") == 123
