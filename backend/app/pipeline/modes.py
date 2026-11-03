from app.extraction.contract.extractor import Extractor
from app.extraction.contract.schemas import Edge, Entity, ExtractionResult
from app.extraction.llm.extractor import LLMExtractor
from app.extraction.pretrained.extractor import PretrainedFirstExtractor

LEGACY_MODES = {
    "pretrained": "pretrained_only",
    "llm": "llm_with_fallback",
    "llm_fallback": "llm_with_fallback",
}
AUTHORITATIVE_TYPES = {"Phone", "Vehicle", "BankAccount"}


class ExtractionModeExtractor(Extractor):
    def __init__(self, mode: str = "pretrained_only", llm_extractor=None):
        self.mode = LEGACY_MODES.get(mode, mode)
        if self.mode not in {
            "pretrained_only",
            "llm_with_fallback",
            "ensemble",
            "llm_only",
        }:
            raise ValueError(f"Unsupported extraction mode: {mode}")
        self.pretrained = PretrainedFirstExtractor()
        self.llm = llm_extractor or LLMExtractor(
            fallback_on_error=self.mode in {"llm_with_fallback", "ensemble"},
        )

    def extract(self, documents: list[dict]) -> ExtractionResult:
        if self.mode == "pretrained_only":
            return self.pretrained.extract(documents)
        if self.mode == "llm_only":
            return self.llm.extract(documents)
        if self.mode == "llm_with_fallback":
            return self._merge_authoritative(
                self.pretrained.extract(documents),
                self.llm.extract(documents),
            )
        return self._ensemble(documents)

    def _merge_authoritative(
        self,
        pretrained: ExtractionResult,
        llm: ExtractionResult,
    ) -> ExtractionResult:
        entities = list(pretrained.entities)
        for entity in llm.entities:
            if entity.type in AUTHORITATIVE_TYPES:
                continue
            entities.append(entity)
        entities = self._deduplicate_entities(entities)
        entity_keys = {(entity.type, entity.id) for entity in entities}

        deterministic_edges = {
            (
                edge.source_type,
                edge.source_id,
                edge.type,
                edge.target_type,
                edge.target_id,
            )
            for edge in pretrained.edges
        }
        edges = [
            edge for edge in pretrained.edges
        ]
        for edge in llm.edges:
            key = (
                edge.source_type,
                edge.source_id,
                edge.type,
                edge.target_type,
                edge.target_id,
            )
            if key not in deterministic_edges:
                if (
                    (edge.source_type, edge.source_id) in entity_keys
                    and (edge.target_type, edge.target_id) in entity_keys
                ):
                    edges.append(edge)

        diagnostics = dict(llm.diagnostics)
        diagnostics.update({
            "deterministic_authoritative": sorted(AUTHORITATIVE_TYPES),
            "pretrained_entities": len(pretrained.entities),
            "llm_entities": len(llm.entities),
        })
        return ExtractionResult(
            entities=self._deduplicate_entities(entities),
            edges=edges,
            diagnostics=diagnostics,
        )

    def _ensemble(self, documents: list[dict]) -> ExtractionResult:
        pretrained = self.pretrained.extract(documents)
        llm = self.llm.extract(documents)
        result = self._merge_authoritative(pretrained, llm)
        pretrained_keys = {
            (edge.source_type, edge.source_id, edge.type, edge.target_type, edge.target_id)
            for edge in pretrained.edges
        }
        llm_keys = {
            (edge.source_type, edge.source_id, edge.type, edge.target_type, edge.target_id)
            for edge in llm.edges
        }
        disagreements = sorted(
            (
                key
                for key in llm_keys.symmetric_difference(pretrained_keys)
            ),
        )
        disagreement_keys = set(disagreements)
        reviewed_edges: list[Edge] = []
        agreed_keys = llm_keys & pretrained_keys
        for edge in result.edges:
            key = (
                edge.source_type,
                edge.source_id,
                edge.type,
                edge.target_type,
                edge.target_id,
            )
            properties = dict(edge.properties)
            if key in disagreement_keys:
                properties["needs_review"] = True
            if key in agreed_keys:
                properties["ensemble_agreement"] = True
                edge = Edge(
                    source_type=edge.source_type,
                    source_id=edge.source_id,
                    target_type=edge.target_type,
                    target_id=edge.target_id,
                    type=edge.type,
                    properties=properties,
                    evidence=edge.evidence,
                    confidence=min(0.99, edge.confidence + 0.05),
                )
            elif properties.get("needs_review"):
                edge = Edge(
                    source_type=edge.source_type,
                    source_id=edge.source_id,
                    target_type=edge.target_type,
                    target_id=edge.target_id,
                    type=edge.type,
                    properties=properties,
                    evidence=edge.evidence,
                    confidence=edge.confidence,
                )
            reviewed_edges.append(edge)
        result.edges = reviewed_edges
        result.diagnostics["ensemble_disagreements"] = disagreements
        result.diagnostics["ensemble_agreement_count"] = len(llm_keys & pretrained_keys)
        return result

    @staticmethod
    def _deduplicate_entities(entities: list[Entity]) -> list[Entity]:
        unique: dict[tuple[str, str], Entity] = {}
        for entity in entities:
            key = (entity.type, entity.id)
            if key in unique:
                previous = unique[key]
                unique[key] = Entity(
                    type=previous.type,
                    id=previous.id,
                    properties={**previous.properties, **entity.properties},
                    mentions=previous.mentions + entity.mentions,
                )
            else:
                unique[key] = entity
        return list(unique.values())
