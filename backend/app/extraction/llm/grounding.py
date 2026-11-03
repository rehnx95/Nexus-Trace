import re

from app.extraction.common.phone import extract_phones
from app.extraction.common.plate import extract_plates
from app.extraction.contract.schemas import Edge, Entity, Mention
from app.graph.registry import ENTITY_TYPES, validate_edge


def _find_span(text: str, value: str) -> tuple[int, int] | None:
    if not value:
        return None
    match = re.search(re.escape(str(value)), text, re.IGNORECASE)
    if not match:
        return None
    return match.start(), match.end()


def _find_grounded_span(text: str, entity_type: str, entity_id: str) -> tuple[int, int] | None:
    span = _find_span(text, entity_id)
    if span is not None:
        return span
    if entity_type == "Phone":
        _, mentions = extract_phones(text, "llm-grounding")
        for mention in mentions:
            digits = "".join(character for character in mention.text if character.isdigit())
            normalized = f"+91{digits}" if len(digits) == 10 else ""
            if normalized == entity_id:
                return mention.start, mention.end
    if entity_type == "Vehicle":
        _, mentions = extract_plates(text, "llm-grounding")
        for mention in mentions:
            normalized = "".join(
                character
                for character in mention.text.upper()
                if character.isalnum()
            )
            if normalized == entity_id.upper().replace(" ", ""):
                return mention.start, mention.end
    return None


def ground_entities(
    payload: dict,
    text: str,
    document_id: str,
) -> tuple[list[Entity], list[Edge], dict]:
    entities_by_key: dict[tuple[str, str], Entity] = {}
    rejected_entities = []

    for item in payload.get("entities", []):
        if not isinstance(item, dict):
            rejected_entities.append("non-object entity")
            continue
        entity_type = item.get("type")
        entity_id = item.get("id")
        if entity_type not in ENTITY_TYPES or not isinstance(entity_id, str):
            rejected_entities.append(str(item.get("id", "unknown")))
            continue
        entity_id = entity_id.strip()
        span = _find_grounded_span(text, entity_type, entity_id)
        if span is None:
            rejected_entities.append(entity_id)
            continue
        start, end = span
        mention = Mention(
            text[start:end],
            start,
            end,
            "llm",
            0.75,
            "LLM-GROUNDING",
            document_id,
        )
        properties = item.get("properties")
        properties = properties if isinstance(properties, dict) else {}
        entity = Entity(entity_type, entity_id, properties, (mention,))
        key = (entity_type, entity_id)
        if key in entities_by_key:
            previous = entities_by_key[key]
            entities_by_key[key] = Entity(
                entity_type,
                entity_id,
                {**previous.properties, **properties},
                previous.mentions + (mention,),
            )
        else:
            entities_by_key[key] = entity

    entities = list(entities_by_key.values())
    entity_lookup = {(entity.type, entity.id): entity for entity in entities}
    edges: list[Edge] = []
    rejected_edges = []

    for item in payload.get("edges", []):
        if not isinstance(item, dict):
            rejected_edges.append("non-object edge")
            continue
        source_type = item.get("source_type")
        source_id = item.get("source_id")
        target_type = item.get("target_type")
        target_id = item.get("target_id")
        edge_type = item.get("type")
        if not all(isinstance(value, str) for value in (
            source_type,
            source_id,
            target_type,
            target_id,
            edge_type,
        )):
            rejected_edges.append(str(item))
            continue
        if (source_type, source_id) not in entity_lookup:
            rejected_edges.append(f"{source_id} -> {target_id}: missing source entity")
            continue
        if (target_type, target_id) not in entity_lookup:
            rejected_edges.append(f"{source_id} -> {target_id}: missing target entity")
            continue
        if not validate_edge(source_type, edge_type, target_type):
            rejected_edges.append(f"{source_id} -> {target_id}: unregistered edge")
            continue
        source_span = _find_grounded_span(text, source_type, source_id)
        target_span = _find_grounded_span(text, target_type, target_id)
        if source_span is None or target_span is None:
            rejected_edges.append(f"{source_id} -> {target_id}: not grounded")
            continue
        start = min(source_span[0], target_span[0])
        end = max(source_span[1], target_span[1])
        evidence = Mention(
            text[start:end],
            start,
            end,
            "llm",
            0.75,
            "LLM-GROUNDING",
            document_id,
        )
        properties = item.get("properties")
        edges.append(Edge(
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
            type=edge_type,
            properties=properties if isinstance(properties, dict) else {},
            evidence=(evidence,),
            confidence=0.75,
        ))

    diagnostics = {
        "llm_entities": len(entities),
        "llm_edges": len(edges),
        "llm_rejected_entities": rejected_entities,
        "llm_rejected_edges": rejected_edges,
    }
    return entities, edges, diagnostics
