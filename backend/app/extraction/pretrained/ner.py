import re

from app.extraction.contract.schemas import Entity, Mention
from app.extraction.pretrained.gazetteer import find_gazetteer_entities
from app.extraction.pretrained.model_loader import load_pretrained_model


def merge_overlaps(entities: list[dict]) -> list[dict]:
    ordered = sorted(entities, key=lambda item: (item["start"], -(item["end"] - item["start"])))
    merged = []
    for candidate in ordered:
        if (
            merged
            and candidate["start"] < merged[-1]["end"]
            and candidate["start"] >= merged[-1]["start"]
        ):
            continue
        merged.append(candidate)
    return merged


class NerExtractor:
    def __init__(self, model=None, model_status=None):
        if model is None and model_status is None:
            model, model_status = load_pretrained_model()
        self.model = model
        self.model_status = model_status or {}

    def extract(self, text: str, document_id: str) -> tuple[list[Entity], dict]:
        spans = find_gazetteer_entities(text)

        if self.model is not None:
            doc = self.model(text)
            for span in doc.ents:
                entity_type = {
                    "PERSON": "Person",
                    "LOC": "Location",
                    "LOCATION": "Location",
                    "GPE": "Location",
                    "FAC": "Location",
                    "ORG": "Organization",
                    "ORGANIZATION": "Organization",
                    "VEHICLE": "Vehicle",
                    "PHONE": "Phone",
                }.get(span.label_)
                # Phones and vehicles are authoritative regex/validator entities.
                # NER labels may recognize their text, but must not create raw-ID
                # duplicates or bypass deterministic normalization.
                if entity_type in {"Phone", "Vehicle"}:
                    continue
                if entity_type:
                    spans.append({
                        "type": entity_type,
                        "text": span.text,
                        "start": span.start_char,
                        "end": span.end_char,
                        "rule_id": f"SPACY-{span.label_}",
                        "confidence": 0.88,
                    })

        spans = merge_overlaps(spans)
        entities: dict[tuple[str, str], Entity] = {}
        for span in spans:
            value = span["text"].strip()
            if not value:
                continue
            if span["type"] == "Person":
                entity_id = re.sub(r"\s+", " ", value)
            else:
                entity_id = value
            mention = Mention(
                value,
                span["start"],
                span["end"],
                "ner" if span["rule_id"].startswith("SPACY-") else "gazetteer",
                span["confidence"],
                span["rule_id"],
                document_id,
            )
            key = (span["type"], entity_id)
            if key in entities:
                previous = entities[key]
                entities[key] = Entity(
                    type=span["type"],
                    id=entity_id,
                    properties=previous.properties,
                    mentions=previous.mentions + (mention,),
                )
            else:
                display_property = {
                    "Person": "name",
                    "Location": "name",
                    "Organization": "name",
                }[span["type"]]
                entities[key] = Entity(
                    type=span["type"],
                    id=entity_id,
                    properties={display_property: entity_id},
                    mentions=(mention,),
                )
        return list(entities.values()), dict(self.model_status)
