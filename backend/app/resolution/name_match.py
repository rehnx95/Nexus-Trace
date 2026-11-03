import re
import unicodedata
from difflib import SequenceMatcher

from app.extraction.common.names import strip_name_honorific

INDIAN_ALIASES = {
    "mohd": "mohammed",
    "md": "mohammed",
    "muhammad": "mohammed",
    "mohammad": "mohammed",
    "sarma": "sharma",
    "sarmah": "sharma",
}


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKC", strip_name_honorific(value)).lower()
    value = re.sub(r"[^\w\s]", " ", value)
    tokens = value.split()
    if tokens:
        tokens[0] = INDIAN_ALIASES.get(tokens[0], tokens[0])
    return " ".join(tokens)


def name_score(left: str, right: str) -> float:
    left_tokens = normalize_name(left).split()
    right_tokens = normalize_name(right).split()
    if not left_tokens or not right_tokens:
        return 0.0
    if normalize_name(left) == normalize_name(right):
        return 100.0

    left_initials = "".join(token[0] for token in left_tokens)
    right_initials = "".join(token[0] for token in right_tokens)
    surname_match = left_tokens[-1] == right_tokens[-1]

    if surname_match and left_initials == right_initials:
        return 96.0
    if surname_match and (
        len(left_tokens) == 1
        or len(right_tokens) == 1
        or left_tokens[0][0] == right_tokens[0][0]
    ):
        return 88.0

    normalized_score = SequenceMatcher(
        None,
        normalize_name(left),
        normalize_name(right),
    ).ratio()
    token_score = len(set(left_tokens) & set(right_tokens)) / max(
        len(set(left_tokens)),
        len(set(right_tokens)),
    )
    return round((normalized_score * 0.55 + token_score * 0.45) * 100, 2)
