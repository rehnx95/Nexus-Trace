import hashlib

from app.extraction.contract.extractor import Extractor
from app.extraction.contract.schemas import ExtractionResult
from app.extraction.pretrained.extractor import PretrainedFirstExtractor

from .grounding import ground_entities
from .parser import parse_llm_json
from .prompts import build_extraction_prompt
from .provider import LLMProvider, OpenAICompatibleProvider


class LLMExtractor(Extractor):
    def __init__(self, provider: LLMProvider | None = None, fallback_on_error: bool = True):
        self.provider = provider or OpenAICompatibleProvider()
        self.fallback_on_error = fallback_on_error

    def extract(self, documents: list[dict]) -> ExtractionResult:
        entities = []
        edges = []
        diagnostics = {"documents": [], "llm_status": "not_run"}
        fallback_needed = False

        for document in documents:
            filename = document["filename"]
            text = document["text"]
            document_id = hashlib.sha256(text.encode("utf-8")).hexdigest()
            diagnostics["documents"].append({
                "filename": filename,
                "document_id": document_id,
            })
            try:
                content = self.provider.complete(build_extraction_prompt(text))
                payload = parse_llm_json(content)
                grounded_entities, grounded_edges, grounding = ground_entities(
                    payload,
                    text,
                    document_id,
                )
                entities.extend(grounded_entities)
                edges.extend(grounded_edges)
                diagnostics["llm_" + document_id] = grounding
                if self.fallback_on_error and not grounded_entities and text.strip():
                    raise ValueError("LLM output contained no grounded entities")
                if diagnostics["llm_status"] == "not_run":
                    diagnostics["llm_status"] = "ok"
            except Exception as exc:
                diagnostics["llm_status"] = "fallback" if self.fallback_on_error else "error"
                diagnostics["llm_error"] = f"{type(exc).__name__}: {exc}"
                fallback_needed = True

        if fallback_needed and self.fallback_on_error:
            fallback = PretrainedFirstExtractor().extract(documents)
            diagnostics.update(fallback.diagnostics)
            diagnostics["llm_status"] = "fallback"
            entities = fallback.entities
            edges = fallback.edges
        else:
            unique_entities = {
                (entity.type, entity.id): entity
                for entity in entities
            }
            entities = list(unique_entities.values())

        return ExtractionResult(entities=entities, edges=edges, diagnostics=diagnostics)


class LlmExtractor(LLMExtractor):
    pass
