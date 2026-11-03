import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.resolution.clustering import resolve_names


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def score_pairs(records: list[dict]) -> dict:
    expected_same = [record for record in records if record["same_entity"]]
    false_auto_merges = 0
    true_auto_merges = 0
    true_review_or_auto = 0

    for record in records:
        result = resolve_names(
            [record["left"], record["right"]],
            alias_pairs=[(record["left"], record["right"])] if record.get("alias") else None,
        )
        decision = result["decisions"][0]["decision"] if result["decisions"] else "keep_separate"
        if record["same_entity"]:
            if decision == "auto_merge":
                true_auto_merges += 1
            if decision in {"auto_merge", "review"}:
                true_review_or_auto += 1
        elif decision == "auto_merge":
            false_auto_merges += 1

    auto_merges = true_auto_merges + false_auto_merges
    return {
        "pairs": len(records),
        "true_pairs": len(expected_same),
        "auto_merges": auto_merges,
        "true_auto_merges": true_auto_merges,
        "false_auto_merges": false_auto_merges,
        "false_merge_rate": round(false_auto_merges / auto_merges, 4) if auto_merges else 0.0,
        "same_entity_auto_plus_review_recall": (
            round(true_review_or_auto / len(expected_same), 4) if expected_same else 0.0
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    records = load_jsonl(args.dev)
    result = {"metrics": score_pairs(records), "inputs": {"dev": str(args.dev)}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
