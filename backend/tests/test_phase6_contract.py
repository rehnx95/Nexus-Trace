from app.extraction.contract.schemas import Entity
from app.extraction.pretrained.extractor import PretrainedFirstExtractor
from app.extraction.pretrained.relations import RelationExtractor
from app.extraction.pretrained.relations.rules import load_relation_rules
from app.graph.registry import validate_edge


def test_relation_rules_load_with_embedded_examples():
    rules = load_relation_rules()
    assert rules
    for rule in rules:
        assert rule["id"]
        assert rule["type"]
        assert rule["positive"]
        assert rule["negative"]
        assert rule["_patterns"]


def test_passive_and_active_relationship_direction():
    person_a = Entity(type="Person", id="Rohan Sharma", properties={"name": "Rohan Sharma"})
    person_b = Entity(type="Person", id="Nisha Rao", properties={"name": "Nisha Rao"})
    organization = Entity(type="Organization", id="Nova Traders Limited")
    extractor = RelationExtractor()

    active = extractor.extract(
        "Rohan Sharma transferred Rs. 55,000 to Nisha Rao.",
        [person_a, person_b],
        "phase6-active",
    )
    assert any(
        edge.type == "FINANCIAL_TRAIL"
        and edge.source_id == "Rohan Sharma"
        and edge.target_id == "Nisha Rao"
        for edge in active
    )

    passive = extractor.extract(
        "Rs. 55,000 was transferred to Nisha Rao by Rohan Sharma.",
        [person_a, person_b],
        "phase6-passive",
    )
    assert any(
        edge.type == "FINANCIAL_TRAIL"
        and edge.source_id == "Rohan Sharma"
        and edge.target_id == "Nisha Rao"
        for edge in passive
    )

    owned = extractor.extract(
        "Rohan Sharma owns KA01AB1234.",
        [
            person_a,
            Entity(type="Vehicle", id="KA01AB1234", properties={"plate": "KA01AB1234"}),
        ],
        "phase6-owned",
    )
    assert any(edge.type == "OWNS_VEHICLE" for edge in owned)

    negative = extractor.extract(
        "Rohan Sharma and Nisha Rao were interviewed separately.",
        [person_a, person_b],
        "phase6-negative",
    )
    assert negative == []

    organization_negative = extractor.extract(
        "Nova Traders Limited was mentioned during the meeting.",
        [person_a, organization],
        "phase6-org-negative",
    )
    assert organization_negative == []


def test_relationship_registry_accepts_financial_accounts():
    assert validate_edge(
        "BankAccount",
        "FINANCIAL_TRAIL",
        "BankAccount",
    )


def test_financial_table_edges_are_aggregated():
    result = PretrainedFirstExtractor().extract([
        {
            "filename": "transactions.csv",
            "text": (
                "from_account,to_account,amount,timestamp\n"
                "123456789012,987654321098,1000,2025-01-01\n"
                "123456789012,987654321098,2500,2025-01-02\n"
            ),
        },
    ])
    edge = next(
        edge
        for edge in result.edges
        if edge.type == "FINANCIAL_TRAIL"
    )
    assert edge.confidence == 1.0
    assert edge.properties["txn_count"] == 2
    assert edge.properties["total_amount"] == 3500.0
