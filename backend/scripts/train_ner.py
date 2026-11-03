import argparse
import json
import random
from pathlib import Path

import spacy
from spacy.training import Example


LABELS = ("PERSON", "LOCATION", "ORGANIZATION", "VEHICLE", "PHONE")
TYPE_MAP = {
    "Person": "PERSON",
    "Location": "LOCATION",
    "Organization": "ORGANIZATION",
    "Vehicle": "VEHICLE",
    "Phone": "PHONE",
}


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8-sig") as source:
        for line in source:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def make_examples(nlp, rows):
    examples = []
    for row in rows:
        annotations = []
        for entity in row.get("entities", []):
            label = TYPE_MAP.get(entity["type"])
            if not label:
                continue
            annotations.append((int(entity["start"]), int(entity["end"]), label))
        examples.append(Example.from_dict(nlp.make_doc(row["text"]), {"entities": annotations}))
    return examples


def evaluate(nlp, rows) -> dict:
    scores = nlp.evaluate(make_examples(nlp, rows))
    return {
        "ents_f": scores["ents_f"],
        "ents_p": scores["ents_p"],
        "ents_r": scores["ents_r"],
        "ents_per_type": scores["ents_per_type"],
    }


def main():
    parser = argparse.ArgumentParser(description="Fine-tune the NexusTrace spaCy NER model")
    parser.add_argument("--train", required=True, type=Path)
    parser.add_argument("--dev", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--base", default="en_core_web_sm")
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument("--seed", type=int, default=26189)
    args = parser.parse_args()

    random.seed(args.seed)
    spacy.util.fix_random_seed(args.seed)

    if args.base.lower() == "blank":
        nlp = spacy.blank("en")
    else:
        try:
            nlp = spacy.load(args.base)
        except OSError:
            nlp = spacy.blank("en")

    ner = nlp.get_pipe("ner") if "ner" in nlp.pipe_names else nlp.add_pipe("ner")
    for label in LABELS:
        ner.add_label(label)

    train_rows = load_jsonl(args.train)
    dev_rows = load_jsonl(args.dev)
    train_examples = make_examples(nlp, train_rows)

    nlp.initialize(lambda: train_examples)
    optimizer = nlp.create_optimizer()
    for _ in range(args.iterations):
        random.shuffle(train_examples)
        nlp.update(train_examples, losses={}, sgd=optimizer, drop=0.25)

    scores = evaluate(nlp, dev_rows)
    args.output.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(args.output)

    report = {
        "base_model": args.base,
        "output": str(args.output),
        "train_examples": len(train_rows),
        "dev_examples": len(dev_rows),
        "iterations": args.iterations,
        "scores": scores,
    }
    (args.output / "training_report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
