import re

FIRST_NAMES = {
    "aarav", "abhinav", "aditya", "akash", "anil", "anita", "arjun", "aruna",
    "deepak", "diya", "imran", "kabir", "kiran", "meera", "nisha", "priya",
    "rahul", "rajesh", "ravi", "rohan", "sanjay", "sunita", "vikram",
}
SURNAMES = {
    "das", "iyer", "khan", "kumar", "menon", "nair", "patel", "rao", "sheikh",
    "singh", "sharma", "verma",
}
LOCATIONS = {
    "central market", "east terminal", "hill station", "river road",
    "new delhi", "mumbai", "chennai", "kolkata", "hyderabad", "bengaluru",
    "jaipur", "lucknow", "patna", "kochi",
}
ORG_SUFFIX_PATTERN = re.compile(
    r"\b(?:Ltd|Limited|Pvt\.?\s*Ltd\.?|Corporation|Corp\.?|Finance|Bank|Services|Traders)\b"
)

PERSON_PATTERN = re.compile(r"\b(?:[A-Z][a-z]+\s+[A-Z][a-z]+)\b")


def find_gazetteer_entities(text: str) -> list[dict]:
    results = []
    lower = text.lower()

    for match in PERSON_PATTERN.finditer(text):
        first, surname = (part.lower() for part in match.group(0).split(maxsplit=1))
        surname = surname.split()[0].lower()
        if first in FIRST_NAMES or surname in SURNAMES:
            results.append({
                "type": "Person",
                "text": match.group(0),
                "start": match.start(),
                "end": match.end(),
                "rule_id": "GAZ-PERSON",
                "confidence": 0.92,
            })

    for location in sorted(LOCATIONS, key=len, reverse=True):
        start = 0
        while True:
            found = lower.find(location, start)
            if found < 0:
                break
            results.append({
                "type": "Location",
                "text": text[found:found + len(location)],
                "start": found,
                "end": found + len(location),
                "rule_id": "GAZ-LOCATION",
                "confidence": 0.94,
            })
            start = found + len(location)

    for match in ORG_SUFFIX_PATTERN.finditer(text):
        prefix = text[max(0, match.start() - 80):match.start()]
        prefix_match = re.search(
            r"([A-Z][A-Za-z0-9&.'-]*(?:\s+[A-Z][A-Za-z0-9&.'-]*){0,6})\s*$",
            prefix,
        )
        prefix_value = prefix_match.group(1).strip() if prefix_match else ""
        value = " ".join(part for part in (prefix_value, match.group(0).strip()) if part).strip()
        value_start = max(0, match.start() - len(prefix_value))
        if len(prefix_value) > 0:
            value_start = text.rfind(prefix_value, 0, match.start())
        results.append({
            "type": "Organization",
            "text": value,
            "start": value_start,
            "end": match.end(),
            "rule_id": "SUFFIX-ORG",
            "confidence": 0.90,
        })

    unique = {(item["type"], item["start"], item["end"]): item for item in results}
    return sorted(unique.values(), key=lambda item: (item["start"], item["end"]))
