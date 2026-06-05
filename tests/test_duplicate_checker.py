import pandas as pd
import pytest
from sheetguard.core.duplicate_checker import DuplicateChecker
from sheetguard.models.rules import RuleSet, ColumnRule, DuplicateRule

@pytest.fixture
def duplicate_rule_set():
    return RuleSet(
        rule_name="Test Duplicates",
        columns=[
            ColumnRule(field_id="id", column="ID"),
            ColumnRule(field_id="name", column="Name"),
        ],
        duplicate_rules=[
            DuplicateRule(name="Exact ID", fields=["id"], match_mode="exact"),
            DuplicateRule(name="Composite Name/ID", fields=["id", "name"], match_mode="exact")
        ]
    )

def test_duplicate_checker_exact(duplicate_rule_set):
    df = pd.DataFrame({
        "ID": ["101", "102", "101", "103", "102"],
        "Name": ["John", "Jane", "John", "Bob", "Alice"]
    })
    
    checker = DuplicateChecker(duplicate_rule_set)
    groups = checker.find_duplicates(df)
    
    # Exact ID rule should find: (101: 0, 2) and (102: 1, 4)
    id_groups = [g for g in groups if g.rule_name == "Exact ID"]
    assert len(id_groups) == 2
    assert {0, 2} in [set(g.row_indices) for g in id_groups]
    assert {1, 4} in [set(g.row_indices) for g in id_groups]
    
    # Composite Name/ID rule should find: (101, John: 0, 2)
    # (102, Jane) and (102, Alice) are NOT duplicates
    comp_groups = [g for g in groups if g.rule_name == "Composite Name/ID"]
    assert len(comp_groups) == 1
    assert set(comp_groups[0].row_indices) == {0, 2}

def test_duplicate_checker_fuzzy():
    rs = RuleSet(
        rule_name="Fuzzy Test",
        columns=[ColumnRule(field_id="name", column="Name")],
        duplicate_rules=[DuplicateRule(name="Fuzzy Name", fields=["name"], match_mode="fuzzy", fuzzy_threshold=80)]
    )
    df = pd.DataFrame({
        "Name": ["John Doe", "Jon Doe", "Jane Smith", "Jane Smiht"]
    })
    
    checker = DuplicateChecker(rs)
    groups = checker.find_duplicates(df)
    
    # Should find two groups: (John Doe, Jon Doe) and (Jane Smith, Jane Smiht)
    assert len(groups) == 2
    indices_sets = [set(g.row_indices) for g in groups]
    assert {0, 1} in indices_sets
    assert {2, 3} in indices_sets

def test_duplicate_checker_no_duplicates(duplicate_rule_set):
    df = pd.DataFrame({
        "ID": ["1", "2", "3"],
        "Name": ["A", "B", "C"]
    })
    checker = DuplicateChecker(duplicate_rule_set)
    groups = checker.find_duplicates(df)
    assert len(groups) == 0

def test_duplicates_dataframe(duplicate_rule_set):
    df = pd.DataFrame({
        "ID": ["101", "101"],
        "Name": ["John", "John"]
    })
    checker = DuplicateChecker(duplicate_rule_set)
    groups = checker.find_duplicates(df)
    dup_df = checker.duplicates_dataframe(df, groups)
    
    assert len(dup_df) == 4 # 2 rules * 2 rows each = 4 entries in report
    assert "_duplicate_rule" in dup_df.columns
    assert "_row_number" in dup_df.columns
