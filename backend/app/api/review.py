from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.resolution.review_queue import MergeCandidate, ReviewQueue

router = APIRouter(prefix="/review", tags=["review"])
repository_root = Path(__file__).resolve().parents[3]
feedback_path = repository_root / "datasets" / "feedback" / "resolution-decisions.jsonl"
queue = ReviewQueue(feedback_path)


class MergeCandidateRequest(BaseModel):
    left: str
    right: str
    score: float = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)
    case_ids: list[str] = Field(default_factory=list)


class MergeDecisionRequest(BaseModel):
    status: str


@router.get("/merges")
def list_merges():
    return {"items": queue.list_pending()}

@router.get("/decisions")
def list_decisions():
    return {"items": queue.list_decisions()}

@router.post("/merges")
def add_merge(candidate: MergeCandidateRequest):
    item = MergeCandidate(
        left=candidate.left,
        right=candidate.right,
        score=candidate.score,
        reasons=tuple(candidate.reasons),
        case_ids=tuple(candidate.case_ids),
    )
    return queue.add(item).to_dict()


@router.post("/merges/{left}/{right}")
def decide_merge(left: str, right: str, decision: MergeDecisionRequest):
    if not queue.decide(left, right, decision.status):
        raise HTTPException(status_code=404, detail="Merge candidate not found")
    return {"left": left, "right": right, "status": decision.status}
