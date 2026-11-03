import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if not args.dev.exists():
        print(f"Dev JSONL not found: {args.dev}", file=sys.stderr)
        return 2

    records = []
    with args.dev.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            annotations = [
                [entity["start"], entity["end"], entity["type"]]
                for entity in record.get("entities", [])
                if entity["type"] in {"Person", "Location", "Organization"}
            ]
            records.append({"text": record["text"], "entities": annotations})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} NER records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
