import json
from pathlib import Path

from app.extraction.pretrained.extractor import PretrainedFirstExtractor
from app.resolution.cross_case import CrossCaseResolver

ROOT = Path(__file__).resolve().parents[2]
DEMO_ROOT = ROOT / "datasets" / "demo"


def test_phase8_demo_fixtures_are_stable():
    for case_dir in sorted(DEMO_ROOT.iterdir()):
        if not case_dir.is_dir():
            continue
        report = (case_dir / "report.txt").read_text(encoding="utf-8")
        expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))
        result = PretrainedFirstExtractor().extract([
            {"filename": "report.txt", "text": report},
        ])
        actual_ids = {entity.id for entity in result.entities}
        missing = set(expected["entity_ids"]) - actual_ids
        assert not missing, (case_dir.name, sorted(missing))
        actual_edge_types = {edge.type for edge in result.edges}
        assert set(expected["edge_types"]) <= actual_edge_types


def test_phase8_demo_alias_cross_case_is_resolved():
    resolver = CrossCaseResolver()
    entities = [
        {"type": "Person", "id": "Arjun Iyer"},
        {"type": "Person", "id": "A. Iyer"},
        {"type": "Phone", "id": "+919876543210"},
    ]
    links = resolver.resolve(entities)
    assert any(
        decision["decision"] in {"auto_merge", "review"}
        and decision["left"] in {"Arjun Iyer", "A. Iyer"}
        and decision["right"] in {"Arjun Iyer", "A. Iyer"}
        for decision in links
    )
