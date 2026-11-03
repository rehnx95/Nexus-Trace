import os

from app.extraction.contract.schemas import ExtractionResult
from app.extraction.pretrained.coverage import calculate_coverage
from app.graph.writer import GraphWriter
from app.pipeline.modes import ExtractionModeExtractor
from app.resolution.aliases import extract_alias_pairs
from app.resolution.clustering import resolve_names


class IngestionOrchestrator:
    def __init__(self, writer: GraphWriter):
        extraction_mode = os.getenv(
            "EXTRACTION_MODE",
            "pretrained_only",
        ).strip().lower()
        self.extractor = ExtractionModeExtractor(extraction_mode)
        self.writer = writer

    def run(
        self,
        case_id: str,
        documents: list[dict],
        append_mode: bool = False,
    ) -> tuple[ExtractionResult, dict]:
        result = self.extractor.extract(documents)
        person_names = {
            entity.id for entity in result.entities if entity.type == "Person"
        }
        alias_pairs = []
        for document in documents:
            alias_pairs.extend(extract_alias_pairs(document["text"]))
        alias_pairs = sorted(set(alias_pairs))
        person_names.update(
            name
            for left, right in alias_pairs
            for name in (left, right)
        )
        person_names = sorted(person_names)
        resolution = resolve_names(
            person_names,
            alias_pairs=alias_pairs,
        ) if person_names else {
            "clusters": [],
            "decisions": [],
        }
        resolution["aliases"] = alias_pairs
        entity_ids = {entity.id for entity in result.entities}
        connected_ids = {
            edge.source_id for edge in result.edges
        } | {edge.target_id for edge in result.edges}
        coverage = calculate_coverage(
            " ".join(document["text"] for document in documents),
            list(entity_ids),
            list(connected_ids),
        )
        coverage["needs_review"] = coverage["score"] < 0.70 or bool(
            resolution.get("decisions")
            and any(item["decision"] == "review" for item in resolution["decisions"])
        )
        result.diagnostics["coverage"] = coverage
        result.diagnostics["resolution"] = resolution
        write_summary = self.writer.write(
            case_id,
            result.entities,
            result.edges,
            replace=not append_mode,
        )
        return result, write_summary
