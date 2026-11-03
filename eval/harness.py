import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.extraction.llm.extractor import LLMExtractor
from app.extraction.pretrained.extractor import PretrainedFirstExtractor


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def score_set(records: list[dict], mode: str = "pretrained") -> dict:
    expected_entities = {
        (record["id"], entity["type"], entity["id"])
        for record in records
        for entity in record["entities"]
    }
    expected_relations = {
        (
            record["id"],
            relation["source_type"],
            relation["source_id"],
            relation["type"],
            relation["target_type"],
            relation["target_id"],
        )
        for record in records
        for relation in record["relations"]
    }

    canonical_mode = {
        "pretrained": "pretrained_only",
        "llm": "llm_with_fallback",
        "llm_fallback": "llm_with_fallback",
    }.get(mode, mode)
    if canonical_mode == "pretrained_only":
        extractor = PretrainedFirstExtractor()
    elif canonical_mode in {"llm_with_fallback", "llm_only"}:
        extractor = LLMExtractor(
            fallback_on_error=canonical_mode == "llm_with_fallback",
        )
    elif canonical_mode == "ensemble":
        from app.pipeline.modes import ExtractionModeExtractor
        extractor = ExtractionModeExtractor(canonical_mode)
    else:
        raise ValueError(f"Unsupported extraction mode: {mode}")
    predicted_entities = set()
    predicted_relations = set()
    expected_ner = {
        (record["id"], entity["type"], entity["start"], entity["end"])
        for record in records
        for entity in record["entities"]
        if entity["type"] in {"Person", "Location", "Organization"}
    }
    predicted_ner = set()
    for record in records:
        result = extractor.extract([{"filename": record["id"] + ".txt", "text": record["text"]}])
        for entity in result.entities:
            predicted_entities.add((record["id"], entity.type, entity.id))
            if entity.type in {"Person", "Location", "Organization"}:
                for mention in entity.mentions:
                    predicted_ner.add((record["id"], entity.type, mention.start, mention.end))
        for relation in result.edges:
            predicted_relations.add(
                (
                    record["id"],
                    relation.source_type,
                    relation.source_id,
                    relation.type,
                    relation.target_type,
                    relation.target_id,
                )
            )

    def prf(expected: set, predicted: set):
        true_positive = len(expected & predicted)
        precision = true_positive / len(predicted) if predicted else 0.0
        recall = true_positive / len(expected) if expected else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }

    return {
        "entity": prf(expected_entities, predicted_entities),
        "ner": prf(expected_ner, predicted_ner),
        "relation": prf(expected_relations, predicted_relations),
        "counts": {
            "expected_entities": len(expected_entities),
            "predicted_entities": len(predicted_entities),
            "expected_relations": len(expected_relations),
            "predicted_relations": len(predicted_relations),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--phase", type=int, default=4)
    parser.add_argument(
        "--mode",
        choices=[
            "pretrained_only",
            "llm_with_fallback",
            "ensemble",
            "llm_only",
            "pretrained",
            "llm",
            "llm_fallback",
        ],
        default="pretrained_only",
    )
    args = parser.parse_args()

    records = load_jsonl(args.dev / "reports.jsonl")
    metrics = score_set(records, args.mode)
    result = {
        "phase": args.phase,
        "records": len(records),
        "metrics": metrics,
        "inputs": {
            "dev": str(args.dev),
        },
        "digest": hashlib.sha256(
            json.dumps(records, sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    destination = args.output / f"phase{args.phase}-dev.json"
    destination.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
