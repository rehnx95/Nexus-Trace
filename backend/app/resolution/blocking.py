from app.resolution.name_match import normalize_name
from app.resolution.phonetic import phonetic_key


def blocking_keys(name: str) -> set[str]:
    normalized = normalize_name(name)
    if not normalized:
        return set()
    tokens = normalized.split()
    keys = {f"phonetic:{phonetic_key(normalized)}", f"prefix:{tokens[0][:2]}"}
    if tokens[-1] != tokens[0]:
        keys.add(f"surname:{tokens[-1]}")
    return keys


def generate_candidate_pairs(names: list[str]) -> list[tuple[str, str]]:
    buckets: dict[str, list[str]] = {}
    for name in names:
        for key in blocking_keys(name):
            buckets.setdefault(key, []).append(name)

    candidates = set()
    for bucket in buckets.values():
        unique_names = sorted(set(bucket))
        for index, left in enumerate(unique_names):
            for right in unique_names[index + 1:]:
                candidates.add(tuple(sorted((left, right))))
    return sorted(candidates)
