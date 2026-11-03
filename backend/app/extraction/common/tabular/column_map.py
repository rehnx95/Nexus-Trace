import re

ALIASES = {
    "from_account": {
        "from account",
        "from_account",
        "sender",
        "payer",
        "debit account",
        "source account",
    },
    "to_account": {
        "to account",
        "to_account",
        "receiver",
        "beneficiary",
        "credit account",
        "destination account",
    },
    "amount": {"amount", "transaction amount", "value", "debit", "credit"},
    "currency": {"currency", "ccy"},
    "timestamp": {"timestamp", "date", "time", "datetime", "transaction date"},
}


def normalize_header(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower().replace("_", " ")).replace("-", " ")


def map_columns(headers: list[str]) -> dict[str, int]:
    mapped = {}
    for index, header in enumerate(headers):
        normalized = normalize_header(header)
        for field, aliases in ALIASES.items():
            if normalized in aliases:
                mapped[field] = index
                break
    return mapped
