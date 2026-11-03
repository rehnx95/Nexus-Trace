from app.extraction.contract.schemas import Edge, Entity
from app.extraction.pretrained.coverage import calculate_coverage
from app.graph.store import InMemoryGraphStore
from app.graph.writer import GraphWriter


def test_coverage_flags_low_relation_coverage():
    result = calculate_coverage(
        "Rohan Sharma met at Central Market. Nisha Rao was interviewed later.",
        ["Rohan Sharma", "Nisha Rao", "Central Market"],
        ["Rohan Sharma", "Central Market"],
    )
    assert result["sentences_with_entities"] == 2
    assert result["sentences_with_entities_no_relation"] >= 1
    assert result["needs_review"] is True


def test_repeated_graph_writes_are_idempotent():
    store = InMemoryGraphStore()
    writer = GraphWriter(store)
    person = Entity(type="Person", id="Rohan Sharma")
    location = Entity(type="Location", id="Central Market")
    edge = Edge(
        source_type="Person",
        source_id="Rohan Sharma",
        target_type="Location",
        target_id="Central Market",
        type="SPOTTED_AT",
        confidence=0.88,
    )

    writer.write("case-7", [person, location], [edge], replace=True)
    writer.write("case-7", [person, location], [edge], replace=False)

    assert len(store.entities["case-7"]) == 2
    assert len(store.edges["case-7"]) == 1
