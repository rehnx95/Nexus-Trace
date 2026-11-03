import re

from app.extraction.common.normalize import normalize_plate
from app.extraction.contract.schemas import Mention

PLATE_PATTERN = re.compile(
    r"(?<![A-Z0-9])([A-Z]{2})[\s-]?(\d{2})[\s-]?([A-Z]{1,3})[\s-]?(\d{1,4})(?![A-Z0-9])",
    re.IGNORECASE,
)


def extract_plates(text: str, document_id: str) -> tuple[list[dict], list[Mention]]:
    entities: list[dict] = []
    mentions: list[Mention] = []
    for match in PLATE_PATTERN.finditer(text):
        plate = normalize_plate(match.group(0))
        start, end = match.span()
        entities.append({"type": "Vehicle", "id": plate, "properties": {"plate": plate}})
        mentions.append(
            Mention(match.group(0).strip(), start, end, "regex", 0.98, "IN-PLATE-BH", document_id)
        )
    unique = {entity["id"]: entity for entity in entities}
    return list(unique.values()), mentions
