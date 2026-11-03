import re

DATE_PATTERN = re.compile(
    r"\b(?:\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b"
)


def extract_dates(text: str) -> list[dict]:
    return [{"text": match.group(0), "start": match.start(), "end": match.end()}
            for match in DATE_PATTERN.finditer(text)]
