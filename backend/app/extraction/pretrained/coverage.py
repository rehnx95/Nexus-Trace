import re


def calculate_coverage(text: str, entity_ids: list[str], edge_ids: list[str]) -> dict:
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text)
        if sentence.strip()
    ]
    entity_ids = sorted(set(entity_ids))
    edge_ids = sorted(set(edge_ids))
    with_entities = [
        sentence
        for sentence in sentences
        if any(entity_id.lower() in sentence.lower() for entity_id in entity_ids)
    ]
    without_relation = [
        sentence
        for sentence in with_entities
        if not any(entity_id.lower() in sentence.lower() for entity_id in edge_ids)
    ]
    score = (
        1.0 - len(without_relation) / len(with_entities)
        if with_entities
        else 1.0
    )
    return {
        "score": round(score, 4),
        "sentences": len(sentences),
        "sentences_with_entities": len(with_entities),
        "sentences_with_entities_no_relation": len(without_relation),
        "unconnected_entities": len(set(entity_ids) - set(edge_ids)),
        "needs_review": score < 0.70,
    }
