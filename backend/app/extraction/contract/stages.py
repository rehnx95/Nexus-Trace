from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.extraction.contract.schemas import Edge, Entity


@dataclass(frozen=True)
class Document:
    document_id: str
    filename: str
    text: str
    source_units: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class Candidate:
    source_entity: Entity
    target_entity: Entity
    relation_type: str | None = None
    trigger_text: str = ""
    features: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScoredRelation:
    edge: Edge
    score: float


@dataclass(frozen=True)
class Abstain:
    candidate: Candidate
    reason: str
    score: float


@dataclass(frozen=True)
class ResolutionResult:
    entities: list[Entity]
    decisions: list[dict] = field(default_factory=list)


class EntityRecognizer(ABC):
    @abstractmethod
    def recognize(self, document: Document) -> list[Entity]:
        raise NotImplementedError


class CandidateGenerator(ABC):
    @abstractmethod
    def generate(self, document: Document, entities: list[Entity]) -> list[Candidate]:
        raise NotImplementedError


class RelationScorer(ABC):
    @abstractmethod
    def score(self, candidate: Candidate) -> ScoredRelation | Abstain:
        raise NotImplementedError


class Resolver(ABC):
    @abstractmethod
    def resolve(
        self,
        entities: list[Entity],
        known: list[Entity] | None = None,
    ) -> ResolutionResult:
        raise NotImplementedError
