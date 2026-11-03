import re

from app.extraction.contract.schemas import Mention

PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+91[\s-]?|91[\s-]?|0)?([6-9](?:[\s-]?\d){9})(?!\d)")


def extract_phones(text: str, document_id: str) -> tuple[list[dict], list[Mention]]:
    entities: list[dict] = []
    mentions: list[Mention] = []
    for match in PHONE_PATTERN.finditer(text):
        local = re.sub(r"[\s-]", "", match.group(1))
        phone_id = "+91" + local
        start, end = match.span()
        entities.append({"type": "Phone", "id": phone_id, "properties": {"number": phone_id}})
        mentions.append(
            Mention(match.group(0), start, end, "regex", 0.99, "IN-PHONE-E164", document_id)
        )

    unique = {entity["id"]: entity for entity in entities}
    return list(unique.values()), mentions
