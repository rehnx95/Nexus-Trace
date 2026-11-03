ENTITY_TYPES = {
    "Person": {"id", "name"},
    "Location": {"id", "name"},
    "Organization": {"id", "name"},
    "Vehicle": {"id", "plate"},
    "Phone": {"id", "number"},
    "BankAccount": {"id", "account_number", "kind"},
}

RELATIONSHIPS = {
    "INTERCEPTED_CALL": {("Phone", "Phone")},
    "ASSOCIATE_OF": {("Person", "Person")},
    "FINANCIAL_TRAIL": {
        ("Person", "Person"),
        ("Phone", "Phone"),
        ("Person", "Organization"),
        ("BankAccount", "BankAccount"),
    },
    "SPOTTED_AT": {("Person", "Location")},
    "OWNS_VEHICLE": {("Person", "Vehicle")},
    "USES_DEVICE": {("Person", "Phone")},
}


def validate_entity(entity_type: str) -> bool:
    return entity_type in ENTITY_TYPES


def validate_edge(source_type: str, edge_type: str, target_type: str) -> bool:
    return (source_type, target_type) in RELATIONSHIPS.get(edge_type, set())
