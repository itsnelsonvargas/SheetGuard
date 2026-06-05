import pandas as pd
import pytest
from sheetguard.utils.column_utils import (
    column_letter_to_index,
    resolve_column_name,
    coerce_cell
)

def test_column_letter_to_index():
    assert column_letter_to_index("A") == 0
    assert column_letter_to_index("Z") == 25
    assert column_letter_to_index("AA") == 26
    assert column_letter_to_index("AB") == 27
    assert column_letter_to_index("  f  ") == 5

def test_resolve_column_name_by_header():
    df = pd.DataFrame(columns=["Name", "Age", "City"])
    assert resolve_column_name(df, "Age") == "Age"
    assert resolve_column_name(df, "City") == "City"

def test_resolve_column_name_by_letter():
    df = pd.DataFrame(columns=["Name", "Age", "City"])
    assert resolve_column_name(df, "A") == "Name"
    assert resolve_column_name(df, "B") == "Age"
    assert resolve_column_name(df, "C") == "City"

def test_resolve_column_name_by_index_string():
    df = pd.DataFrame(columns=["Name", "Age", "City"])
    assert resolve_column_name(df, "0") == "Name"
    assert resolve_column_name(df, "1") == "Age"
    assert resolve_column_name(df, "2") == "City"

def test_resolve_column_name_not_found():
    df = pd.DataFrame(columns=["Name", "Age"])
    with pytest.raises(KeyError, match="Column 'City' not found"):
        resolve_column_name(df, "City")
    with pytest.raises(KeyError, match="Column 'D' not found"):
        resolve_column_name(df, "D")
    with pytest.raises(KeyError, match="Column '5' not found"):
        resolve_column_name(df, "5")

def test_coerce_cell():
    assert coerce_cell(123) == 123
    assert coerce_cell("abc") == "abc"
    assert coerce_cell(pd.NA) == ""
    assert coerce_cell(None) == ""
    import numpy as np
    assert coerce_cell(np.nan) == ""
    # Test with a value that has .item() (like numpy types)
    val = np.int64(10)
    assert coerce_cell(val) == 10
