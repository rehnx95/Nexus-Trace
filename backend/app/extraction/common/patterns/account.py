import re

from app.extraction.common.normalize import normalize_account, normalize_upi

ACCOUNT_PATTERN = re.compile(
    r"(?i)\b(?:bank\s+account|account(?:\s+(?:number|no\.?))?|a/c)\s*[:#]?\s*([\d][\d\s-]{8,17}\d)\b"
)
UPI_PATTERN = re.compile(r"\b[a-z0-9._-]{2,64}@[a-z]{2,32}\b", re.IGNORECASE)


def extract_accounts(text: str) -> list[dict]:
    found: dict[str, dict] = {}
    for match in ACCOUNT_PATTERN.finditer(text):
        account = normalize_account(match.group(1))
        if account:
            found.setdefault(account, {"type": "BankAccount", "id": account,
                                       "kind": "account", "text": match.group(1)})
    for match in UPI_PATTERN.finditer(text):
        upi = normalize_upi(match.group(0))
        if upi:
            found.setdefault(upi, {"type": "BankAccount", "id": upi,
                                   "kind": "upi", "text": match.group(0)})
    return list(found.values())
