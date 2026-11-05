import json
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    records = []
    with Path(path).open("r", encoding="utf-8-sig") as source:
        for line in source:
            if line.strip():
                records.append(json.loads(line))
    return records


def _metrics(predicted: set, expected: set) -> dict:
    true_positive = len(predicted & expected)
    precision = true_positive / len(predicted) if predicted else 0.0
    recall = true_positive / len(expected) if expected else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def score_set(records: list[dict]) -> dict:
    predicted_entities = set()
    expected_entities = set()
    predicted_spans = set()
    expected_spans = set()
    predicted_relations = set()
    expected_relations = set()

    for record in records:
        text = record["text"]
        for entity in record.get("entities", []):
            expected_entities.add((entity["type"], entity["id"]))
            span_text = text[entity["start"]:entity["end"]]
            expected_spans.add((entity["start"], entity["end"], entity["type"], span_text))
        for relation in record.get("relations", []):
            expected_relations.add((
                relation["source_type"] if "source_type" in relation else relation["head"],
                relation["type"],
                relation["target_type"] if "target_type" in relation else relation["tail"],
                relation.get("directed", True),
            ))

    return {
        "entity": _metrics(predicted_entities, expected_entities),
        "ner": _metrics(predicted_spans, expected_spans),
        "relation": _metrics(predicted_relations, expected_relations),
        "counts": {
            "records": len(records),
            "expected_entities": len(expected_entities),
            "expected_relations": len(expected_relations),
        },
    }
