import argparse
import json
import random
from pathlib import Path


FIRST_NAMES = [
    "Aarav", "Nisha", "Rohan", "Diya", "Meera", "Imran", "Kabir",
    "Priya", "Arjun", "Kiran", "Zoya", "Vikram", "Sana", "Anil",
]
LAST_NAMES = [
    "Patel", "Rao", "Singh", "Iyer", "Khan", "Das", "Menon", "Sheikh",
    "Sharma", "Nair", "Kapoor", "Verma", "Bose", "Gupta",
]
LOCATIONS = [
    "Central Market", "River Road", "East Terminal", "Court Road",
    "Airport Gate 2", "Railway Station", "Lake View", "Industrial Area",
    "South Bus Stand", "Old Town", "Silver Bridge", "North Plaza",
]
VEHICLES = ["KA05MH1234", "DL01GH3456", "MH12CD5678", "TN09EF9012"]


def add_entity(entities, text, value, entity_type, start):
    if start >= 0:
        entities.append({
            "type": entity_type,
            "text": value,
            "start": start,
            "end": start + len(value),
        })


def main():
    parser = argparse.ArgumentParser(description="Generate labeled NER training examples")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--count", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=26189)
    args = parser.parse_args()

    random.seed(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    positive_templates = [
        "{person} uses phone {phone} and was seen at {location}.",
        "{person} owns vehicle {vehicle}.",
        "{person} was spotted near {location} with vehicle {vehicle}.",
        "Records list {person}, contact number {phone}, and location {location}.",
        "Vehicle {vehicle} belonging to {person} was parked at {location}.",
        "Call record connects {person} using phone {phone} to {location}.",
        "{person} visited {location} in vehicle {vehicle}.",
        "The device registered to {person} has number {phone}.",
    ]
    negative_templates = [
        "{person} and {other} were interviewed; no link was established.",
        "Records mention {person}, {location}, and {vehicle}, but do not connect them.",
        "{vehicle} and phone {phone} appear in separate reports.",
        "There is no evidence linking {person} to {location}.",
        "The investigator noted unrelated references to {location} and {vehicle}.",
    ]

    with args.output.open("w", encoding="utf-8") as output:
        for index in range(args.count):
            person = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            other = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            location = random.choice(LOCATIONS)
            vehicle = random.choice(VEHICLES)
            phone = "".join(str(random.randint(7, 9)) for _ in range(10))

            if index % 4 == 0:
                template = random.choice(negative_templates)
                text = template.format(
                    person=person, other=other, location=location,
                    vehicle=vehicle, phone=phone,
                )
                entities = []
                for entity_type, value in (
                    ("Person", person),
                    ("Person", other),
                    ("Location", location),
                    ("Vehicle", vehicle),
                    ("Phone", phone),
                ):
                    start = text.find(value)
                    if start >= 0:
                        add_entity(entities, text, value, entity_type, start)
            else:
                text = random.choice(positive_templates).format(
                    person=person, location=location, vehicle=vehicle, phone=phone,
                )
                entities = []
                for entity_type, value in (
                    ("Person", person),
                    ("Location", location),
                    ("Vehicle", vehicle),
                    ("Phone", phone),
                ):
                    start = text.find(value)
                    if start >= 0:
                        add_entity(entities, text, value, entity_type, start)

            output.write(json.dumps({
                "id": f"ner-generated-{index:05d}",
                "text": text,
                "entities": entities,
            }) + "\n")


if __name__ == "__main__":
    main()
