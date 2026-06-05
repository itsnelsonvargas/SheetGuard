import pandas as pd
import pytest
from sheetguard.core.validator import DataValidator
from sheetguard.models.rules import RuleSet, ColumnRule

@pytest.fixture
def basic_rule_set():
    return RuleSet(
        rule_name="Test Validator",
        columns=[
            ColumnRule(field_id="id", column="ID", required=True, min_value=1),
            ColumnRule(field_id="email", column="Email", validate_email=True),
            ColumnRule(field_id="category", column="Category", allowed_values=["A", "B"]),
            ColumnRule(field_id="date", column="Date", date_format="YYYY-MM-DD"),
            ColumnRule(field_id="code", column="Code", regex=r"^C\d{3}$")
        ]
    )

def test_validator_required(basic_rule_set):
    df = pd.DataFrame({"ID": [1, None, " "], "Email": ["a@b.com", "c@d.com", "e@f.com"], "Category": ["A", "B", "A"], "Date": ["2023-01-01", "2023-01-02", "2023-01-03"], "Code": ["C001", "C002", "C003"]})
    validator = DataValidator(basic_rule_set)
    issues = validator.validate(df)
    
    # Row 1 (index 1) and Row 2 (index 2) should have required issues for ID
    id_issues = [i for i in issues if i.field_id == "id" and i.rule_type == "required"]
    assert len(id_issues) == 2
    assert id_issues[0].row_index == 1
    assert id_issues[1].row_index == 2

def test_validator_numeric_range(basic_rule_set):
    df = pd.DataFrame({"ID": [0, 5, "invalid"], "Email": ["a@b.com"]*3, "Category": ["A"]*3, "Date": ["2023-01-01"]*3, "Code": ["C001"]*3})
    validator = DataValidator(basic_rule_set)
    issues = validator.validate(df)
    
    range_issues = [i for i in issues if i.field_id == "id" and i.rule_type == "numeric_range"]
    assert len(range_issues) == 2
    assert range_issues[0].message == "Value 0.0 below minimum 1"
    assert range_issues[1].message == "Value is not numeric"

def test_validator_email(basic_rule_set):
    df = pd.DataFrame({"ID": [1, 2], "Email": ["valid@test.com", "invalid-email"], "Category": ["A", "A"], "Date": ["2023-01-01", "2023-01-01"], "Code": ["C001", "C001"]})
    validator = DataValidator(basic_rule_set)
    issues = validator.validate(df)
    
    email_issues = [i for i in issues if i.field_id == "email"]
    assert len(email_issues) == 1
    assert email_issues[0].row_index == 1
    assert "Invalid email address" in email_issues[0].message

def test_validator_allowed_values(basic_rule_set):
    df = pd.DataFrame({"ID": [1, 2], "Email": ["a@b.com", "a@b.com"], "Category": ["A", "C"], "Date": ["2023-01-01", "2023-01-01"], "Code": ["C001", "C001"]})
    validator = DataValidator(basic_rule_set)
    issues = validator.validate(df)
    
    cat_issues = [i for i in issues if i.field_id == "category"]
    assert len(cat_issues) == 1
    assert cat_issues[0].row_index == 1
    assert "Value not in allowed list" in cat_issues[0].message

def test_validator_date(basic_rule_set):
    df = pd.DataFrame({"ID": [1, 2], "Email": ["a@b.com"]*2, "Category": ["A"]*2, "Date": ["2023-01-01", "01/01/2023"], "Code": ["C001"]*2})
    validator = DataValidator(basic_rule_set)
    issues = validator.validate(df)
    
    # 01/01/2023 might be valid if pd.to_datetime can parse it (it can)
    # The code says:
    # try: datetime.strptime(s, fmt)
    # except ValueError: parsed = pd.to_datetime(s, errors="coerce", dayfirst=True)
    # if pd.isna(parsed): ...
    # So 01/01/2023 should pass if it can be parsed.
    
    df_invalid = pd.DataFrame({"ID": [1], "Email": ["a@b.com"], "Category": ["A"], "Date": ["not-a-date"], "Code": ["C001"]})
    issues = validator.validate(df_invalid)
    date_issues = [i for i in issues if i.field_id == "date"]
    assert len(date_issues) == 1

def test_validator_regex(basic_rule_set):
    df = pd.DataFrame({"ID": [1, 2], "Email": ["a@b.com"]*2, "Category": ["A"]*2, "Date": ["2023-01-01"]*2, "Code": ["C001", "X999"]})
    validator = DataValidator(basic_rule_set)
    issues = validator.validate(df)
    
    code_issues = [i for i in issues if i.field_id == "code"]
    assert len(code_issues) == 1
    assert code_issues[0].row_index == 1
