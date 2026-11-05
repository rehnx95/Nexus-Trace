from app.core.config import ontology_config


_ONTOLOGY = ontology_config()
ENTITY_TYPES = _ONTOLOGY["entities"]
RELATIONSHIPS = {
    relation_type: {tuple(pair) for pair in pairs}
    for relation_type, pairs in _ONTOLOGY["relationships"].items()
}


def validate_entity(entity_type: str) -> bool:
    return entity_type in ENTITY_TYPES


def validate_edge(source_type: str, edge_type: str, target_type: str) -> bool:
    return (source_type, target_type) in RELATIONSHIPS.get(edge_type, set())
