import json

from app.extraction.llm.extractor import LLMExtractor
from app.extraction.llm.grounding import ground_entities
from app.extraction.llm.parser import parse_llm_json
from app.graph.registry import validate_edge
from app.pipeline.modes import ExtractionModeExtractor


class MockProvider:
    def __init__(self, content):
        self.content = content

    def complete(self, prompt: str) -> str:
        return self.content


def test_phase9_llm_output_is_contract_compatible_and_grounded():
    text = "Arjun Iyer uses phone 9876543210 and was seen at Central Market."
    provider = MockProvider(json.dumps({
        "entities": [
            {"type": "Person", "id": "Arjun Iyer"},
            {"type": "Phone", "id": "+919876543210"},
            {"type": "Location", "id": "Central Market"},
        ],
        "edges": [
            {
                "source_type": "Person",
                "source_id": "Arjun Iyer",
                "target_type": "Phone",
                "target_id": "+919876543210",
                "type": "USES_DEVICE",
            },
        ],
    }))
    result = LLMExtractor(provider=provider).extract([
        {"filename": "report.txt", "text": text},
    ])

    assert {entity.id for entity in result.entities} == {
        "Arjun Iyer",
        "+919876543210",
        "Central Market",
    }
    assert result.edges[0].type == "USES_DEVICE"
    assert result.edges[0].evidence[0].method == "llm"


def test_phase9_hallucinated_entities_and_edges_are_rejected():
    text = "Rohan Sharma was seen at Central Market."
    payload = parse_llm_json(json.dumps({
        "entities": [
            {"type": "Person", "id": "Rohan Sharma"},
            {"type": "Location", "id": "Central Market"},
            {"type": "Person", "id": "Invented Person"},
        ],
        "edges": [
            {
                "source_type": "Person",
                "source_id": "Rohan Sharma",
                "target_type": "Location",
                "target_id": "Central Market",
                "type": "SPOTTED_AT",
            },
            {
                "source_type": "Person",
                "source_id": "Invented Person",
                "target_type": "Location",
                "target_id": "Central Market",
                "type": "SPOTTED_AT",
            },
        ],
    }))
    entities, edges, diagnostics = ground_entities(payload, text, "doc-1")

    assert {entity.id for entity in entities} == {"Rohan Sharma", "Central Market"}
    assert len(edges) == 1
    assert diagnostics["llm_rejected_entities"] == ["Invented Person"]


def test_phase9_unregistered_edges_remain_disallowed():
    assert validate_edge("Person", "SPOTTED_AT", "Location")
    assert not validate_edge("Person", "DOES_NOT_EXIST", "Location")


class EmptyProvider:
    def complete(self, prompt: str) -> str:
        return '{"entities":[],"edges":[]}'


def test_phase9_llm_fallback_replaces_mixed_batch():
    result = LLMExtractor(provider=EmptyProvider()).extract([
        {"filename": "report.txt", "text": "Arjun Iyer uses phone 9876543210."},
        {"filename": "empty.txt", "text": ""},
    ])

    assert result.diagnostics["llm_status"] == "fallback"
    assert "Arjun Iyer" in {entity.id for entity in result.entities}


def test_phase9_pretrained_only_never_calls_llm():
    class UnexpectedProvider:
        def complete(self, prompt: str) -> str:
            raise AssertionError("LLM must not run")

    mode = ExtractionModeExtractor(
        "pretrained_only",
        llm_extractor=LLMExtractor(provider=UnexpectedProvider()),
    )
    result = mode.extract([
        {"filename": "report.txt", "text": "Vehicle KA05MH1234 used phone 9876543210."},
    ])

    assert {entity.id for entity in result.entities} >= {
        "KA05MH1234",
        "+919876543210",
    }


def test_phase9_llm_mode_preserves_pretrained_non_identifier_entities():
    class PersonOnlyProvider:
        def complete(self, prompt: str) -> str:
            return json.dumps({
                "entities": [{"type": "Person", "id": "Arjun Iyer"}],
                "edges": [],
            })

    mode = ExtractionModeExtractor(
        "llm_with_fallback",
        llm_extractor=LLMExtractor(provider=PersonOnlyProvider()),
    )
    result = mode.extract([
        {
            "filename": "report.txt",
            "text": "Arjun Iyer was seen at Central Market.",
        },
    ])

    ids = {entity.id for entity in result.entities}
    assert "Arjun Iyer" in ids
    assert "Central Market" in ids
