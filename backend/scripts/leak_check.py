import argparse
import hashlib
import json
from pathlib import Path


def normalized(text: str) -> str:
    return " ".join(text.lower().split())


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8-sig") as source:
        for line in source:
            if line.strip():
                row = json.loads(line)
                rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Check training data leakage")
    parser.add_argument("splits", nargs="+", type=Path)
    args = parser.parse_args()

    owners = {}
    errors = []
    for split_path in args.splits:
        rows = load_jsonl(split_path)
        for row in rows:
            sentence_hash = hashlib.sha256(
                normalized(row["text"]).encode("utf-8")
            ).hexdigest()
            if sentence_hash in owners:
                errors.append(
                    f"Duplicate sentence across {owners[sentence_hash]} and "
                    f"{split_path}: {row['id']}"
                )
            else:
                owners[sentence_hash] = str(split_path)

            if not isinstance(row.get("entities"), list):
                errors.append(f"{row['id']}: entities must be a list")
            if not isinstance(row.get("relations"), list):
                errors.append(f"{row['id']}: relations must be a list")

    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    print(f"Leak check passed for {len(args.splits)} splits.")


if __name__ == "__main__":
    main()
