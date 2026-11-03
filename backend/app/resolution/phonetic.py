import re
import unicodedata

from app.resolution.name_match import normalize_name

INDIAN_NORMALIZATIONS = {
    "kh": "k",
    "gh": "k",
    "sh": "s",
    "bh": "b",
    "dh": "d",
    "th": "t",
}


def phonetic_key(value: str) -> str:
    normalized = normalize_name(value)
    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = normalized.encode("ascii", "ignore").decode()
    normalized = normalized.replace(" ", "")
    normalized = re.sub(r"([a-z])\1+", r"\1", normalized)
    for source, target in INDIAN_NORMALIZATIONS.items():
        normalized = normalized.replace(source, target)
    normalized = re.sub(r"[aeiou]", "", normalized)
    return normalized[:12] or "unknown"
