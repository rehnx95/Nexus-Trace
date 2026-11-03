import json
from hashlib import sha256
from threading import Lock

from app.resolution.clustering import resolve_names


class CrossCaseResolver:
    def __init__(self):
        self._cache: dict[str, list[dict]] = {}
        self._lock = Lock()

    def resolve(self, case_entities: list[dict]) -> list[dict]:
        digest = sha256(
            json.dumps(case_entities, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        with self._lock:
            if digest in self._cache:
                return list(self._cache[digest])

        names = sorted({
            entity["id"]
            for entity in case_entities
            if entity["type"] == "Person"
        })
        result = resolve_names(names, auto_threshold=93.0, review_threshold=88.0)
        links = [
            {
                "left": decision["left"],
                "right": decision["right"],
                "score": decision["score"],
                "decision": decision["decision"],
                "reasons": decision["reasons"],
            }
            for decision in result["decisions"]
            if decision["decision"] != "keep_separate"
        ]
        with self._lock:
            self._cache[digest] = links
        return list(links)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
