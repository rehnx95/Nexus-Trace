import re
from decimal import Decimal, InvalidOperation


def normalize_digits(value: str) -> str:
    return "".join(character for character in value if character.isdigit())


def normalize_plate(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", value).upper()


def normalize_phone(value: str) -> str | None:
    digits = normalize_digits(value)
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    if len(digits) != 10 or digits[0] not in "6789":
        return None
    return "+91" + digits


def normalize_account(value: str) -> str | None:
    digits = normalize_digits(value)
    if 9 <= len(digits) <= 18:
        return digits
    return None


def normalize_upi(value: str) -> str | None:
    candidate = value.strip().lower()
    match = re.fullmatch(r"[a-z0-9._-]{2,64}@[a-z]{2,32}", candidate)
    return candidate if match else None


def normalize_amount(value: str, default_currency: str = "INR") -> tuple[Decimal, str] | None:
    text = value.strip().upper()
    currency = default_currency
    if text.startswith("RS"):
        currency = "INR"
        text = text[2:].strip(". ")
    elif text.startswith("₹") or text.startswith("INR"):
        currency = "INR"
        text = re.sub(r"^(₹|INR)\s*", "", text, flags=re.IGNORECASE)
    elif text.startswith("$"):
        currency = "USD"
        text = text[1:].strip()
    elif text.startswith("EUR") or text.startswith("€"):
        currency = "EUR"
        text = re.sub(r"^(EUR|€)\s*", "", text, flags=re.IGNORECASE)

    text = text.replace(",", "").replace(" ", "")
    text = re.sub(r"(?i)(crore|cr|lakh|lac|k)$", lambda match: "", text)
    multiplier_match = re.search(r"(crore|cr|lakh|lac|k)$", value.strip(), re.IGNORECASE)
    multipliers = {"crore": Decimal("10000000"), "cr": Decimal("10000000"),
                   "lakh": Decimal("100000"), "lac": Decimal("100000"),
                   "k": Decimal("1000")}
    multiplier = Decimal("1")
    if multiplier_match:
        multiplier = multipliers[multiplier_match.group(0).lower()]
        text = re.sub(r"(?i)(crore|cr|lakh|lac|k)$", "", text)
    try:
        return Decimal(text) * multiplier, currency
    except InvalidOperation:
        return None
