import argparse
import json
import random
from pathlib import Path


FAMILIES = ("ownership", "sighting", "transfer", "association", "negative")
DEV_FAMILIES = {"sighting", "association"}

TRAIN_NAMES = [
    "Aarav Menon",
    "Diya Iyer",
    "Kabir Khan",
    "Meera Singh",
]
DEV_NAMES = [
    "Rohan Patel",
    "Nisha Rao",
    "Imran Sheikh",
    "Priya Das",
]
LOCATIONS = ("Central Market", "River Road", "East Terminal", "Hill Station")
PLATES = ("KA05AB1234", "MH12CD5678", "TN09EF9012", "DL01GH3456")
PHONES = ("9876543210", "9123456789", "9988776655", "9765432108")


def entity(entity_type: str, entity_id: str, text_value: str, start: int, end: int):
    return {
        "type": entity_type,
        "id": entity_id,
        "text": text_value,
        "start": start,
        "end": end,
    }


def make_report(index: int, family: str, rng: random.Random):
    names = DEV_NAMES if family in DEV_FAMILIES else TRAIN_NAMES
    first = rng.choice(names)
    second = rng.choice([name for name in names if name != first])
    phone = rng.choice(PHONES)
    plate = rng.choice(PLATES)
    location = rng.choice(LOCATIONS)

    if family == "ownership":
        text = f"Investigator noted that {first} owns vehicle {plate}."
        targets = [
            entity("Person", first, first, text.index(first), text.index(first) + len(first)),
            entity("Vehicle", plate, plate, text.index(plate), text.index(plate) + len(plate)),
        ]
        relations = [{
            "source_type": "Person",
            "source_id": first,
            "target_type": "Vehicle",
            "target_id": plate,
            "type": "OWNS_VEHICLE",
        }]
    elif family == "sighting":
        text = f"{first} was seen at {location} while carrying a vehicle bearing {plate}."
        targets = [
            entity("Person", first, first, text.index(first), text.index(first) + len(first)),
            entity("Location", location, location, text.index(location), text.index(location) + len(location)),
        ]
        relations = [{
            "source_type": "Person",
            "source_id": first,
            "target_type": "Location",
            "target_id": location,
            "type": "SPOTTED_AT",
        }]
    elif family == "transfer":
        text = f"Rs. 55,000 was transferred to {second} by {first}; call record {phone}."
        targets = [
            entity("Person", first, first, text.index(first), text.index(first) + len(first)),
            entity("Person", second, second, text.index(second), text.index(second) + len(second)),
            entity("Phone", "+91" + phone, phone, text.index(phone), text.index(phone) + len(phone)),
        ]
        relations = [{
            "source_type": "Person",
            "source_id": first,
            "target_type": "Person",
            "target_id": second,
            "type": "FINANCIAL_TRAIL",
        }]
    elif family == "association":
        text = f"{first} and {second} were interviewed separately in connection with the inquiry."
        targets = [
            entity("Person", first, first, text.index(first), text.index(first) + len(first)),
            entity("Person", second, second, text.index(second), text.index(second) + len(second)),
        ]
        relations = []
    else:
        text = f"Both {first} and {second} were present, but neither admitted a relationship."
        targets = [
            entity("Person", first, first, text.index(first), text.index(first) + len(first)),
            entity("Person", second, second, text.index(second), text.index(second) + len(second)),
        ]
        relations = []

    return {
        "id": f"synthetic-{index:04d}",
        "text": text,
        "entities": targets,
        "relations": relations,
        "family": family,
        "split": "dev" if family in DEV_FAMILIES else "train",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=26189)
    parser.add_argument("--count", type=int, default=40)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)

    records = [
        make_report(index, FAMILIES[index % len(FAMILIES)], rng)
        for index in range(args.count)
    ]
    dev = [record for record in records if record["split"] == "dev"]
    train = [record for record in records if record["split"] == "train"]

    for split, rows in (("train", train), ("dev", dev)):
        destination = args.output / split
        destination.mkdir(parents=True, exist_ok=True)
        with (destination / "reports.jsonl").open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(json.dumps({"train": len(train), "dev": len(dev), "total": len(records)}))


if __name__ == "__main__":
    main()
