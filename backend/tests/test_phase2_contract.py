import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from eval.harness import load_jsonl, score_set  # noqa: E402


def test_gold_dev_layout_is_valid():
    records = load_jsonl(ROOT / "datasets" / "gold" / "dev" / "reports.jsonl")
    assert len(records) == 6
    for record in records:
        assert record["split"] == "dev"
        for entity in record["entities"]:
            assert 0 <= entity["start"] < entity["end"] <= len(record["text"])
            assert record["text"][entity["start"]:entity["end"]] == entity["text"]


def test_phase2_harness_returns_metrics():
    records = load_jsonl(ROOT / "datasets" / "gold" / "dev" / "reports.jsonl")
    metrics = score_set(records)
    assert set(metrics) == {"entity", "ner", "relation", "counts"}
    assert set(metrics["entity"]) == {"precision", "recall", "f1"}
