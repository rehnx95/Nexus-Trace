from app.resolution.aliases import extract_alias_pairs
from app.resolution.blocking import generate_candidate_pairs
from app.resolution.clustering import resolve_names
from app.resolution.cross_case import CrossCaseResolver
from app.resolution.identifiers import IdentifierEvidence
from app.resolution.name_match import name_score, normalize_name
from app.resolution.phonetic import phonetic_key
from app.resolution.review_queue import MergeCandidate, ReviewQueue


def test_name_normalization_initials_and_alias_variants():
    assert normalize_name("Shri Mohd. Sharma") == "mohammed sharma"
    assert name_score("Rohan Sharma", "R. Sharma") >= 88
    assert name_score("Mohd Khan", "Mohammed Khan") == 100


def test_blocking_is_bounded_and_phonetic():
    names = ["Rohan Sharma", "R. Sharma", "Priya Das"]
    pairs = generate_candidate_pairs(names)
    assert ("R. Sharma", "Rohan Sharma") in pairs
    assert phonetic_key("Sharma") == phonetic_key("Sarma")


def test_shared_identifier_goes_review_not_auto_merge():
    evidence = {
        "Rohan Sharma": IdentifierEvidence(phone={"+919876543210"}),
        "Rohan S Sharma": IdentifierEvidence(phone={"+919876543210"}),
    }
    result = resolve_names(list(evidence), evidence=evidence)
    pair = next(iter(result["decisions"]))
    assert pair["decision"] == "review"
    assert "shared_identifier_review" in pair["reasons"]


def test_identifier_conflict_blocks_auto_merge():
    evidence = {
        "Rohan Sharma": IdentifierEvidence(phone={"+919876543210"}),
        "Rohan S Sharma": IdentifierEvidence(phone={"+919123456789"}),
    }
    result = resolve_names(list(evidence), evidence=evidence)
    pair = next(item for item in result["decisions"])
    assert pair["decision"] == "keep_separate"
    assert "identifier_constraint" in pair["reasons"]


def test_alias_markers_create_explicit_candidates():
    assert ("Rohan Sharma", "Ronny Sharma") in extract_alias_pairs(
        "Rohan Sharma alias Ronny Sharma was questioned."
    )
    assert ("Nisha Rao", "N. Rao") in extract_alias_pairs(
        "Nisha Rao also known as N. Rao appeared."
    )
    result = resolve_names(
        ["Nisha Rao", "N. Rao"],
        alias_pairs=[("Nisha Rao", "N. Rao")],
    )
    assert result["canonical_names"]
    assert result["decisions"][0]["reasons"] == ["explicit_alias"]


def test_review_queue_and_cross_case_cache():
    queue = ReviewQueue()
    candidate = MergeCandidate("Asha Khan", "Asha K.", 91.0, ("phonetic_match",))
    queue.add(candidate)
    assert len(queue.list_pending()) == 1
    assert queue.decide("Asha Khan", "Asha K.", "rejected")
    assert queue.list_pending() == []

    resolver = CrossCaseResolver()
    entities = [{"type": "Person", "id": "Rohan Sharma"}, {"type": "Phone", "id": "+91"}]
    first = resolver.resolve(entities)
    assert resolver.resolve(entities) == first


def test_review_decisions_persist_and_reload(tmp_path):
    feedback_path = tmp_path / "resolution-decisions.jsonl"
    queue = ReviewQueue(feedback_path)
    queue.add(MergeCandidate("Dev Rao", "D. Rao", 91.0, ("phonetic_match",)))
    assert queue.decide("Dev Rao", "D. Rao", "approved")

    reloaded = ReviewQueue(feedback_path)
    assert reloaded.list_decisions()[0]["status"] == "approved"
