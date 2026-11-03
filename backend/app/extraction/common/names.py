import re

HONORIFIC_PATTERN = re.compile(
    r"^\s*(?:mr|mrs|ms|miss|shri|smt|dr|adv)\.?\s+",
    re.IGNORECASE,
)
RELATIVE_PATTERN = re.compile(r"\b(?:S/?o|D/?o|W/?o)\s*[.:]?\s*", re.IGNORECASE)


def strip_name_honorific(name: str) -> str:
    cleaned = HONORIFIC_PATTERN.sub("", name.strip())
    return " ".join(cleaned.split())


def split_relative_alias(name: str) -> tuple[str, str | None]:
    match = RELATIVE_PATTERN.search(name)
    if not match:
        return strip_name_honorific(name), None
    person = strip_name_honorific(name[:match.start()])
    relation = name[match.end():].strip()
    return person, relation or None
