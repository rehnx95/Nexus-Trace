from app.resolution.blocking import generate_candidate_pairs
from app.resolution.identifiers import IdentifierEvidence
from app.resolution.name_match import name_score, normalize_name
from app.resolution.phonetic import phonetic_key


def resolve_names(
    names: list[str],
    evidence: dict[str, IdentifierEvidence] | None = None,
    auto_threshold: float = 97.0,
    review_threshold: float = 88.0,
    alias_pairs: list[tuple[str, str]] | None = None,
) -> dict:
    evidence = evidence or {}
    decisions: dict[tuple[str, str], dict] = {}
    explicit_aliases = {
        tuple(sorted(pair))
        for pair in (alias_pairs or [])
        if pair[0] in names and pair[1] in names
    }

    for left, right in generate_candidate_pairs(names):
        score = name_score(left, right)
        pair_key = tuple(sorted((left, right)))
        if pair_key in explicit_aliases:
            score = max(score, 100.0)
        left_evidence = evidence.get(left, IdentifierEvidence())
        right_evidence = evidence.get(right, IdentifierEvidence())
        reasons = []
        if pair_key in explicit_aliases:
            reasons.append("explicit_alias")
        if phonetic_key(left) == phonetic_key(right):
            reasons.append("phonetic_match")
        if left_evidence.has_shared_identifier(right_evidence):
            reasons.append("shared_identifier_review")

        if left_evidence.has_conflict(right_evidence):
            decision = "keep_separate"
            reasons.append("identifier_constraint")
        elif left_evidence.has_shared_identifier(right_evidence):
            decision = "review"
        elif score >= auto_threshold:
            decision = "auto_merge"
        elif score >= review_threshold:
            decision = "review"
        else:
            decision = "keep_separate"
        decisions[tuple(sorted((left, right)))] = {
            "decision": decision,
            "score": score,
            "reasons": reasons,
        }

    parent = {name: name for name in set(names)}

    def find(name: str) -> str:
        while parent[name] != name:
            parent[name] = parent[parent[name]]
            name = parent[name]
        return name

    def union(left: str, right: str) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for pair, decision in decisions.items():
        if decision["decision"] == "auto_merge":
            union(*pair)
        elif tuple(pair) in explicit_aliases and decision["decision"] != "keep_separate":
            union(*pair)

    grouped: dict[str, list[str]] = {}
    for name in sorted(parent):
        grouped.setdefault(find(name), []).append(name)

    canonical_names: dict[str, str] = {}
    for root, cluster in grouped.items():
        canonical_names[root] = min(
            cluster,
            key=lambda name: (-len(normalize_name(name).split()), name.lower()),
        )

    return {
        "clusters": sorted(
            (sorted(cluster) for cluster in grouped.values()),
            key=lambda item: item[0],
        ),
        "canonical_names": canonical_names,
        "decisions": [
            {"left": pair[0], "right": pair[1], **decision}
            for pair, decision in sorted(decisions.items())
        ],
    }
