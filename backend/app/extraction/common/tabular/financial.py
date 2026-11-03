import csv
import io

from app.extraction.common.normalize import normalize_account, normalize_amount
from app.extraction.common.tabular.column_map import map_columns
from app.extraction.common.tabular.format_detect import detect_format


def parse_amount(value: str) -> tuple[str, str] | None:
    normalized = normalize_amount(value)
    if not normalized:
        return None
    amount, currency = normalized
    if amount < 0:
        return None
    return format(amount, "f"), currency


def parse_financial(text: str, document_id: str) -> tuple[list, list, dict]:
    del document_id
    detected = detect_format(text)
    if detected == "unsupported":
        return [], [], {"format": "unsupported", "valid_rows": 0, "invalid_rows": 0}
    delimiter = "\t" if detected == "tsv" else ";" if detected == "semicolon_csv" else ","
    rows = list(csv.reader(io.StringIO(text.strip()), delimiter=delimiter))
    if len(rows) < 2:
        return [], [], {"format": detected, "valid_rows": 0, "invalid_rows": 0}

    columns = map_columns(rows[0])
    if "from_account" not in columns or "to_account" not in columns or "amount" not in columns:
        return [], [], {"format": detected, "valid_rows": 0, "invalid_rows": 0}

    entities = {}
    transactions = []
    invalid_rows = 0
    valid_rows = 0
    for row in rows[1:]:
        indexes = [columns["from_account"], columns["to_account"], columns["amount"]]
        if max(indexes) >= len(row):
            invalid_rows += 1
            continue
        source = normalize_account(row[columns["from_account"]])
        target = normalize_account(row[columns["to_account"]])
        amount = parse_amount(row[columns["amount"]])
        if not source or not target or not amount or source == target:
            invalid_rows += 1
            continue
        valid_rows += 1
        for account in (source, target):
            entities.setdefault(account, {"type": "BankAccount", "id": account, "kind": "account"})
        transactions.append({
            "from_account": source,
            "to_account": target,
            "amount": amount[0],
            "currency": amount[1],
            "timestamp": (
                row[columns["timestamp"]]
                if "timestamp" in columns and columns["timestamp"] < len(row)
                else None
            ),
        })
    return list(entities.values()), transactions, {
        "format": detected, "valid_rows": valid_rows, "invalid_rows": invalid_rows
    }
