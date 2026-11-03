import re

from app.extraction.common.normalize import normalize_amount

AMOUNT_PATTERN = re.compile(
    r"(?i)\b(?:₹|rs\.?|inr|usd|\$|eur|€)?\s*\d[\d,]*(?:\.\d{1,2})?\s*(?:crore|cr|lakh|lac|k)?\b"
)


def extract_amounts(text: str) -> list[dict]:
    found: list[dict] = []
    for match in AMOUNT_PATTERN.finditer(text):
        value = normalize_amount(match.group(0))
        if value:
            amount, currency = value
            found.append({"amount": str(amount), "currency": currency, "text": match.group(0)})
    return found
