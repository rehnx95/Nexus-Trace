import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.extraction.pretrained.extractor import PretrainedFirstExtractor


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8-sig") as source:
        for line in source:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def entity_keys(entities: list) -> set[tuple[str, str]]:
    return {(entity.type, entity.id) for entity in entities}


def edge_keys(edges: list) -> set[tuple[str, str, str, str, str]]:
    return {
        (
            edge.source_type,
            edge.source_id,
            edge.type,
            edge.target_type,
            edge.target_id,
        )
        for edge in edges
    }


def metrics(predicted: set, expected: set) -> dict:
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
        "predicted": sorted(predicted),
        "expected": sorted(expected),
        "false_positive": sorted(predicted - expected),
        "false_negative": sorted(expected - predicted),
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate NexusTrace extraction on gold JSONL")
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    extractor = PretrainedFirstExtractor()
    aggregate_entities = {"predicted": set(), "expected": set()}
    aggregate_edges = {"predicted": set(), "expected": set()}

    for row in load_jsonl(args.dataset):
        result = extractor.extract([{"filename": f"{row['id']}.txt", "text": row["text"]}])

        aggregate_entities["predicted"].update(entity_keys(result.entities))
        aggregate_entities["expected"].update(
            (entity["type"], entity["id"])
            for entity in row.get("entities", [])
            if entity["type"] != "Phone" or entity["id"].startswith("+")
        )

        aggregate_edges["predicted"].update(edge_keys(result.edges))
        aggregate_edges["expected"].update(
            (
                relation["source_type"],
                relation["source_id"],
                relation["type"],
                relation["target_type"],
                relation["target_id"],
            )
            for relation in row.get("relations", [])
        )

    report = {
        "entity": metrics(
            aggregate_entities["predicted"],
            aggregate_entities["expected"],
        ),
        "relation": metrics(
            aggregate_edges["predicted"],
            aggregate_edges["expected"],
        ),
    }
    print(json.dumps(report, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
