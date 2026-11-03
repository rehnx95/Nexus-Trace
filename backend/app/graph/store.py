from abc import ABC, abstractmethod

from app.extraction.contract.schemas import Edge, Entity
from utils import neo4j_driver as db


class GraphStore(ABC):
    @abstractmethod
    def clear_case(self, case_id: str) -> None:
        pass

    @abstractmethod
    def write_entities(self, case_id: str, entities: list[Entity]) -> int:
        pass

    @abstractmethod
    def write_edges(self, case_id: str, edges: list[Edge]) -> int:
        pass


class InMemoryGraphStore(GraphStore):
    def __init__(self):
        self.entities: dict[str, dict[tuple[str, str], dict]] = {}
        self.edges: dict[str, dict[tuple[str, str, str, str, str], dict]] = {}

    def clear_case(self, case_id: str) -> None:
        self.entities.pop(case_id, None)
        self.edges.pop(case_id, None)

    def write_entities(self, case_id: str, entities: list[Entity]) -> int:
        store = self.entities.setdefault(case_id, {})
        for entity in entities:
            store[(entity.type, entity.id)] = entity.to_dict()
        return len(store)

    def write_edges(self, case_id: str, edges: list[Edge]) -> int:
        store = self.edges.setdefault(case_id, {})
        for edge in edges:
            key = (
                edge.source_type,
                edge.source_id,
                edge.type,
                edge.target_type,
                edge.target_id,
            )
            existing = store.get(key)
            if existing:
                merged = dict(existing["properties"])
                merged.update(edge.properties)
                existing = dict(existing)
                existing["properties"] = merged
                existing["confidence"] = max(existing["confidence"], edge.confidence)
                store[key] = existing
            else:
                store[key] = edge.to_dict()
        return len(store)


class Neo4jGraphStore(GraphStore):
    def clear_case(self, case_id: str) -> None:
        db.query(
            "MATCH (n {case_id: $case_id}) WHERE NOT n:Case DETACH DELETE n",
            {"case_id": case_id},
        )

    def write_entities(self, case_id: str, entities: list[Entity]) -> int:
        if not entities:
            return 0
        count = 0
        for entity in entities:
            label = entity.type
            db.query(
                f"MERGE (n:{label} {{case_id: $case_id, id: $id}}) " "SET n += $properties",
                {
                    "case_id": case_id,
                    "id": entity.id,
                    "properties": entity.properties,
                },
            )
            count += 1
        return count

    def write_edges(self, case_id: str, edges: list[Edge]) -> int:
        if not edges:
            return 0
        rows = [
            {
                "source_type": edge.source_type,
                "source_id": edge.source_id,
                "target_type": edge.target_type,
                "target_id": edge.target_id,
                "type": edge.type,
                "properties": edge.properties,
                "confidence": edge.confidence,
            }
            for edge in edges
        ]
        for row in rows:
            source_label = row["source_type"]
            target_label = row["target_type"]
            relation_type = row["type"]
            db.query(
                f"MATCH (source:{source_label} {{case_id: $case_id, id: $source_id}}) "
                f"MATCH (target:{target_label} {{case_id: $case_id, id: $target_id}}) "
                f"MERGE (source)-[edge:{relation_type}]->(target) "
                "SET edge += $properties, edge.confidence = $confidence",
                {
                    "case_id": case_id,
                    "source_id": row["source_id"],
                    "target_id": row["target_id"],
                    "properties": row["properties"],
                    "confidence": row["confidence"],
                },
            )
        return len(rows)
