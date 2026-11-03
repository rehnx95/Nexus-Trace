import re

ALIAS_PATTERNS = (
    re.compile(
        r"\b([A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){0,2})\s+"
        r"(?:also\s+known\s+as|alias|urf|@|aka)\s+"
        r"([A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){0,2})",
    ),
)


def extract_alias_pairs(text: str) -> list[tuple[str, str]]:
    pairs = set()
    for pattern in ALIAS_PATTERNS:
        for match in pattern.finditer(text):
            left = " ".join(match.group(1).strip().split())
            right = " ".join(match.group(2).strip().split())
            if left and right:
                pairs.add((left, right))
    return sorted(pairs)
