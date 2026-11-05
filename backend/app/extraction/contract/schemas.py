from dataclasses import asdict, dataclass, field
from typing import Literal
import uuid


@dataclass(frozen=True)
class Mention:
    text: str
    start: int
    end: int
    method: Literal[
        "regex", "table", "llm", "ner", "gazetteer",
        "dependency", "rule", "manual",
    ]
    confidence: float
    rule_id: str
    document_id: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Entity:
    type: str
    id: str
    properties: dict = field(default_factory=dict)
    mentions: tuple[Mention, ...] = ()
    uid: str = field(default_factory=lambda: str(uuid.uuid4()))
    aliases: list[str] = field(default_factory=list)
    provenance: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "id": self.id,
            "properties": dict(self.properties),
            "mentions": [mention.to_dict() for mention in self.mentions],
            "uid": self.uid,
            "aliases": list(self.aliases),
            "provenance": dict(self.provenance),
        }


@dataclass(frozen=True)
class Edge:
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    type: str
    properties: dict = field(default_factory=dict)
    evidence: tuple[Mention, ...] = ()
    confidence: float = 1.0
    provenance: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source_type": self.source_type,
            "source_id": self.source_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "type": self.type,
            "properties": dict(self.properties),
            "evidence": [mention.to_dict() for mention in self.evidence],
            "confidence": self.confidence,
            "provenance": dict(self.provenance),
        }


@dataclass
class ExtractionResult:
    entities: list[Entity]
    edges: list[Edge]
    diagnostics: dict = field(default_factory=dict)
    abstained: list[dict] = field(default_factory=list)
    llm_reviewed: bool = False

    def to_dict(self) -> dict:
        return {
            "entities": [entity.to_dict() for entity in self.entities],
            "edges": [edge.to_dict() for edge in self.edges],
            "diagnostics": dict(self.diagnostics),
            "abstained": list(self.abstained),
            "llm_reviewed": self.llm_reviewed,
        }
