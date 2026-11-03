from app.extraction.common.names import split_relative_alias, strip_name_honorific
from app.extraction.common.normalize import (
    normalize_amount,
    normalize_phone,
    normalize_plate,
    normalize_upi,
)
from app.extraction.common.patterns.account import extract_accounts
from app.extraction.common.tabular.financial import parse_financial


def test_identifier_normalization():
    assert normalize_phone("+91 98765 43210") == "+919876543210"
    assert normalize_phone("1234567890") is None
    assert normalize_plate("ka 05 mh 1234") == "KA05MH1234"
    assert normalize_upi("USER@OKAXIS") == "user@okaxis"
    assert normalize_amount("Rs. 1,25,000")[0] == normalize_amount("125000")[0]


def test_account_and_name_patterns():
    accounts = extract_accounts("Transfer from Account No: 1234-5678-9012 to user@okaxis.")
    assert accounts == [
        {"type": "BankAccount", "id": "123456789012", "kind": "account",
         "text": "1234-5678-9012"},
        {"type": "BankAccount", "id": "user@okaxis", "kind": "upi", "text": "user@okaxis"},
    ]
    assert strip_name_honorific("Shri Arun Kumar") == "Arun Kumar"
    assert split_relative_alias("Ravi Kumar S/o Mahesh Kumar")[1] == "Mahesh Kumar"


def test_financial_parser_aliases_and_validation():
    text = (
        "source_account,destination account,transaction amount,transaction date\n"
        "123456789012,987654321098,Rs. 125000,2025-01-02\n"
        "123456789012,bad,1,2025-01-02\n"
        "123456789012,123456789012,500,2025-01-02\n"
    )
    entities, transactions, diagnostics = parse_financial(text, "doc")

    assert {entity["id"] for entity in entities} == {"123456789012", "987654321098"}
    assert diagnostics["valid_rows"] == 1
    assert diagnostics["invalid_rows"] == 2
    assert transactions[0]["amount"] == "125000"
    assert transactions[0]["currency"] == "INR"
