import argparse
import json
import random
from pathlib import Path


SUBJECTS = ["Person A", "Person B", "Person C", "Person D", "Person E"]
LOCATIONS = ["Market Area", "Bus Terminal", "Railway Station", "Court Road", "Airport Gate"]
VEHICLES = ["AB12CD3456", "XY34ZZ7890", "TN09EF9012", "KA05MH1234"]
PHONES = ["9876543210", "9123456789", "9988776655", "9765432108"]
ORGS = ["Regional Bank", "Transport Office", "Local Hospital", "Police Station"]


def span(text: str, value: str) -> tuple[int, int]:
    start = text.find(value)
    return start, start + len(value)


def entity(text: str, entity_type: str, value: str) -> dict:
    start, end = span(text, value)
    return {"type": entity_type, "text": value, "start": start, "end": end}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic relation training data")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--count", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=26189)
    args = parser.parse_args()

    random.seed(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    templates = [
        ("ASSOCIATED_WITH", "{a} was seen with {b}."),
        ("PRESENT_AT", "{a} was seen at {location}."),
        ("PARKED_NEAR", "Vehicle {vehicle} was parked near {location}."),
        ("USES_DEVICE", "{a} uses phone {phone}."),
        ("OWNS", "{a} owns vehicle {vehicle}."),
        ("DRIVES", "{a} drove vehicle {vehicle}."),
        ("WORKS_FOR", "{a} works for {org}."),
        ("MEMBER_OF", "{a} is a member of {org}."),
        ("CALLS", "Phone {phone} called phone {other_phone}."),
        ("MESSAGES", "{phone} sent a message to {other_phone}."),
        ("FINANCIAL_TRAIL", "{a} transferred money to {b}."),
        ("TRAVELLED_WITH", "{a} travelled with {b}."),
        ("REGISTERED_TO", "Vehicle {vehicle} is registered to {a}."),
        ("RESIDES_AT", "{a} resides at {location}."),
        ("LOCATED_AT_TOWER", "Phone {phone} was located at tower near {location}."),
        ("VICTIM_OF", "{a} was the victim of an incident by {org}."),
        ("SUSPECT_IN", "{a} is a suspect in an incident at {location}."),
        ("WITNESS_TO", "{a} witnessed an incident at {location}."),
        ("INVESTIGATED_BY", "{org} investigated the incident involving {other_org}."),
    ]

    negative_templates = [
        "{a} and {b} were interviewed separately.",
        "Records mention {a}, {location}, and {vehicle} but do not connect them.",
        "Phone {phone} and vehicle {vehicle} are unrelated report references.",
        "There is no evidence linking {a} to {org}.",
    ]

    seen_text: set[str] = set()
    with args.output.open("w", encoding="utf-8") as output:
        for index in range(args.count):
            while True:
                a = random.choice(SUBJECTS)
                b = random.choice([item for item in SUBJECTS if item != a])
                location = random.choice(LOCATIONS)
                vehicle = random.choice(VEHICLES)
                phone = random.choice(PHONES)
                other_phone = random.choice([item for item in PHONES if item != phone])
                org = random.choice(ORGS)
                other_org = random.choice([item for item in ORGS if item != org])

                if index % 5 == 0:
                    relation = None
                    text = random.choice(negative_templates).format(
                        a=a, b=b, location=location, vehicle=vehicle,
                        phone=phone, org=org,
                    )
                else:
                    relation, template = random.choice(templates)
                    text = template.format(
                        a=a, b=b, location=location, vehicle=vehicle,
                        phone=phone, other_phone=other_phone, org=org,
                        other_org=other_org,
                    )
                if text not in seen_text:
                    seen_text.add(text)
                    break
            relations = []
            entities = []

            values = {
                "Person": [a, b],
                "Location": [location],
                "Vehicle": [vehicle],
                "Phone": [phone, other_phone],
                "Organization": [org, other_org],
            }
            for entity_type, candidates in values.items():
                for value in candidates:
                    if value and text.find(value) >= 0:
                        entities.append(entity(text, entity_type, value))

            if relation:
                person_entities = [item for item in entities if item["type"] == "Person"]
                location_entities = [item for item in entities if item["type"] == "Location"]
                vehicle_entities = [item for item in entities if item["type"] == "Vehicle"]
                phone_entities = [item for item in entities if item["type"] == "Phone"]
                org_entities = [item for item in entities if item["type"] == "Organization"]
                head = tail = None
                if relation in {"ASSOCIATED_WITH", "FINANCIAL_TRAIL", "TRAVELLED_WITH"} and len(person_entities) >= 2:
                    head, tail = person_entities[0], person_entities[1]
                elif relation in {"PRESENT_AT", "SUSPECT_IN", "WITNESS_TO", "RESIDES_AT"} and person_entities and location_entities:
                    head, tail = person_entities[0], location_entities[0]
                elif relation == "PARKED_NEAR" and vehicle_entities and location_entities:
                    head, tail = vehicle_entities[0], location_entities[0]
                elif relation in {"USES_DEVICE"} and person_entities and phone_entities:
                    head, tail = person_entities[0], phone_entities[0]
                elif relation in {"OWNS", "DRIVES", "REGISTERED_TO"} and person_entities and vehicle_entities:
                    head, tail = person_entities[0], vehicle_entities[0]
                elif relation in {"WORKS_FOR", "MEMBER_OF"} and person_entities and org_entities:
                    head, tail = person_entities[0], org_entities[0]
                elif relation in {"CALLS", "MESSAGES"} and len(phone_entities) >= 2:
                    head, tail = phone_entities[0], phone_entities[1]
                elif relation == "LOCATED_AT_TOWER" and phone_entities and location_entities:
                    head, tail = phone_entities[0], location_entities[0]
                elif relation in {"VICTIM_OF"} and person_entities and org_entities:
                    head, tail = person_entities[0], org_entities[0]
                elif relation == "INVESTIGATED_BY" and len(org_entities) >= 2:
                    head, tail = org_entities[0], org_entities[1]
                if head and tail:
                    relations.append({
                        "head": head["text"],
                        "tail": tail["text"],
                        "type": relation,
                        "directed": True,
                    })

            output.write(json.dumps({
                "id": f"relation-synthetic-{index:05d}",
                "source": "local-synthetic",
                "text": text,
                "entities": entities,
                "relations": relations,
            }) + "\n")


if __name__ == "__main__":
    main()
