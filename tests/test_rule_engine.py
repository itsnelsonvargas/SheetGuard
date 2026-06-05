import json
import pytest
from pathlib import Path
from sheetguard.core.rule_engine import RuleEngine
from sheetguard.models.rules import RuleSet, ColumnRule

@pytest.fixture
def sample_rule_dict():
    return {
        "rule_name": "Test Rule",
        "description": "A test rule set",
        "columns": [
            {
                "field_id": "name",
                "column": "Name",
                "required": True,
                "cleaning": ["trim", "uppercase"]
            },
            {
                "field_id": "age",
                "column": "Age",
                "min_value": 0,
                "max_value": 120
            }
        ],
        "duplicate_rules": [
            {
                "name": "Unique Name",
                "fields": ["Name"],
                "match_mode": "exact"
            }
        ]
    }

def test_rule_engine_validate_valid(sample_rule_dict):
    rs = RuleSet.from_dict(sample_rule_dict)
    # Should not raise
    RuleEngine.validate(rs)

def test_rule_engine_validate_invalid_name(sample_rule_dict):
    sample_rule_dict["rule_name"] = " "
    rs = RuleSet.from_dict(sample_rule_dict)
    with pytest.raises(ValueError, match="rule_name is required"):
        RuleEngine.validate(rs)

def test_rule_engine_validate_no_columns(sample_rule_dict):
    sample_rule_dict["columns"] = []
    rs = RuleSet.from_dict(sample_rule_dict)
    with pytest.raises(ValueError, match="At least one column rule is required"):
        RuleEngine.validate(rs)

def test_rule_engine_validate_duplicate_field_id(sample_rule_dict):
    sample_rule_dict["columns"].append({
        "field_id": "name",
        "column": "Other"
    })
    rs = RuleSet.from_dict(sample_rule_dict)
    with pytest.raises(ValueError, match="Duplicate field_id: name"):
        RuleEngine.validate(rs)

def test_rule_engine_validate_unsupported_cleaning(sample_rule_dict):
    sample_rule_dict["columns"][0]["cleaning"].append("invalid_op")
    rs = RuleSet.from_dict(sample_rule_dict)
    with pytest.raises(ValueError, match="Unsupported cleaning rule: invalid_op"):
        RuleEngine.validate(rs)

def test_rule_engine_clone(sample_rule_dict):
    rs = RuleSet.from_dict(sample_rule_dict)
    cloned = RuleEngine.clone(rs, "Cloned Rule")
    assert cloned.rule_name == "Cloned Rule"
    assert len(cloned.columns) == len(rs.columns)
    assert cloned.columns[0].field_id == rs.columns[0].field_id

def test_rule_engine_save_load(tmp_path, sample_rule_dict):
    rs = RuleSet.from_dict(sample_rule_dict)
    path = tmp_path / "test_rule.json"
    RuleEngine.save(rs, path)
    
    assert path.exists()
    
    loaded = RuleEngine.load(path)
    assert loaded.rule_name == rs.rule_name
    assert len(loaded.columns) == len(rs.columns)
    assert loaded.columns[0].field_id == rs.columns[0].field_id
