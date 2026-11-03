import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock


@dataclass(frozen=True)
class MergeCandidate:
    left: str
    right: str
    score: float
    reasons: tuple[str, ...]
    status: str = "pending"
    case_ids: tuple[str, ...] = ()
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "left": self.left,
            "right": self.right,
            "score": self.score,
            "reasons": list(self.reasons),
            "status": self.status,
            "case_ids": list(self.case_ids),
            "created_at": self.created_at,
        }


class ReviewQueue:
    def __init__(self, feedback_path: str | Path | None = None):
        self._items: dict[tuple[str, str], MergeCandidate] = {}
        self._lock = Lock()
        self._feedback_path = Path(feedback_path) if feedback_path else None
        self._load()

    def _load(self) -> None:
        if self._feedback_path is None:
            return
        if not self._feedback_path.exists():
            return
        with self._feedback_path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                status = item.get("status")
                if status not in {"approved", "rejected", "merged"}:
                    continue
                candidate = MergeCandidate(
                    left=item["left"],
                    right=item["right"],
                    score=float(item["score"]),
                    reasons=tuple(item.get("reasons", [])),
                    status=status,
                    case_ids=tuple(item.get("case_ids", [])),
                    created_at=item.get("created_at", datetime.now(timezone.utc).isoformat()),
                )
                key = tuple(sorted((candidate.left, candidate.right)))
                self._items[key] = candidate

    def _persist(self, item: MergeCandidate) -> None:
        if self._feedback_path is None:
            return
        self._feedback_path.parent.mkdir(parents=True, exist_ok=True)
        with self._feedback_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item.to_dict(), sort_keys=True) + "\n")

    def add(self, candidate: MergeCandidate) -> MergeCandidate:
        key = tuple(sorted((candidate.left, candidate.right)))
        with self._lock:
            self._items[key] = candidate
        return candidate

    def list_pending(self) -> list[dict]:
        with self._lock:
            return [
                item.to_dict()
                for item in sorted(self._items.values(), key=lambda row: -row.score)
                if item.status == "pending"
            ]

    def decide(self, left: str, right: str, status: str) -> bool:
        if status not in {"approved", "rejected", "merged"}:
            return False
        key = tuple(sorted((left, right)))
        with self._lock:
            item = self._items.get(key)
            if not item:
                return False
            self._items[key] = MergeCandidate(
                left=item.left,
                right=item.right,
                score=item.score,
                reasons=item.reasons,
                status=status,
                case_ids=item.case_ids,
                created_at=item.created_at,
            )
            self._persist(self._items[key])
        return True

    def list_decisions(self) -> list[dict]:
        with self._lock:
            return [
                item.to_dict()
                for item in sorted(self._items.values(), key=lambda row: -row.score)
                if item.status != "pending"
            ]
