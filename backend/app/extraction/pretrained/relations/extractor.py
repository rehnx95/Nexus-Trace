import re

from app.extraction.contract.schemas import Edge, Entity, Mention
from app.extraction.pretrained.relations.rules import load_relation_rules
from app.graph.registry import validate_edge


class RelationExtractor:
    def __init__(self, rules_path=None):
        self.rules = load_relation_rules(rules_path)

    def extract(self, text: str, entities: list[Entity], document_id: str) -> list[Edge]:
        edges: list[Edge] = []
        clauses = re.split(r"(?:\n|;\s*)", text)
        entity_by_text: dict[str, Entity] = {}
        for entity in entities:
            for mention in entity.mentions:
                entity_by_text[mention.text.lower()] = entity
            entity_by_text.setdefault(entity.id.lower(), entity)

        for clause in clauses:
            lowered = clause.lower()
            present = [
                (entity, start)
                for text_key, entity in entity_by_text.items()
                if (start := lowered.find(text_key.lower())) >= 0
            ]
            present.sort(key=lambda item: item[1])

            for rule in self.rules:
                if not any(pattern.search(clause) for pattern in rule["_patterns"]):
                    continue
                allowed = {
                    tuple(pair)
                    for pair in rule.get("allowed_types", [])
                }
                source_types = {source for source, _ in allowed}
                target_types = {target for _, target in allowed}
                sources = [item for item in present if item[0].type in source_types]
                targets = [item for item in present if item[0].type in target_types]
                for source, source_position in sources:
                    for target, target_position in targets:
                        if source.type == target.type and source.id == target.id:
                            continue
                        if not validate_edge(source.type, rule["type"], target.type):
                            continue
                        if not self._directional_match(
                            rule,
                            clause,
                            source.id,
                            target.id,
                            lowered,
                            source_position,
                            target_position,
                        ):
                            continue
                        start = max(source_position, 0)
                        end = min(
                            len(clause),
                            max(start, target_position + len(target.id)),
                        )
                        evidence = Mention(
                            clause.strip(),
                            start,
                            end,
                            "regex",
                            float(rule.get("confidence", 0.85)),
                            rule["id"],
                            document_id,
                        )
                        edges.append(Edge(
                            source_type=source.type,
                            source_id=source.id,
                            target_type=target.type,
                            target_id=target.id,
                            type=rule["type"],
                            evidence=(evidence,),
                            confidence=float(rule.get("confidence", 0.85)),
                        ))
        return self._deduplicate(edges)

    @staticmethod
    def _directional_match(
        rule: dict,
        clause: str,
        source_id: str,
        target_id: str,
        lowered: str,
        source_position: int | None = None,
        target_position: int | None = None,
    ) -> bool:
        role = rule.get("role", "subject_object")
        source_pos = (
            source_position
            if source_position is not None
            else lowered.find(source_id.lower())
        )
        target_pos = (
            target_position
            if target_position is not None
            else lowered.find(target_id.lower())
        )
        if source_pos < 0 or target_pos < 0:
            return False
        if role == "passive_agent":
            if " by " not in lowered:
                return False
            source_pos_in_text = lowered.find(source_id.lower())
            by_pos = lowered.rfind(" by ")
            return source_pos_in_text > by_pos and target_pos < by_pos
        if role == "object_source":
            return target_pos < source_pos
        if role == "bidirectional":
            return True
        return source_pos < target_pos

    @staticmethod
    def _deduplicate(edges: list[Edge]) -> list[Edge]:
        grouped: dict[tuple[str, str, str, str, str], Edge] = {}
        for edge in edges:
            key = (
                edge.source_type,
                edge.source_id,
                edge.type,
                edge.target_type,
                edge.target_id,
            )
            if key in grouped:
                previous = grouped[key]
                grouped[key] = Edge(
                    source_type=previous.source_type,
                    source_id=previous.source_id,
                    target_type=previous.target_type,
                    target_id=previous.target_id,
                    type=previous.type,
                    evidence=previous.evidence + edge.evidence,
                    confidence=max(previous.confidence, edge.confidence),
                )
            else:
                grouped[key] = edge
        return list(grouped.values())
